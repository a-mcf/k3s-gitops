"""Mirror the Mealie meal plan into a Radicale calendar.

Mealie owns the household meal plan; this job projects it onto the shared
family calendar so meals show up in everyone's phone calendar app next to
real events. Stateless: every event the mirror writes carries an
X-MEALIE-MIRROR property with a content hash, so each run can identify its
own events, update changed ones, and delete entries removed from the plan —
without ever touching events created directly in Radicale.

Only plan entries inside the sync window (WINDOW_PAST days back to
WINDOW_FUTURE days ahead) are managed; mirrored events older than the
window are left in place as meal history.

Config: config.json — {"mealie_url", "mealie_token", "user", "password",
"collection"}; MIRROR_CONFIG, RADICALE_URL and DRY_RUN come from the
environment.
"""

import base64
import datetime
import hashlib
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET

RADICALE_URL = os.environ.get(
    "RADICALE_URL", "http://radicale.radicale.svc.cluster.local:5232"
)
DRY_RUN = os.environ.get("DRY_RUN", "") == "1"
MARKER = "X-MEALIE-MIRROR"
WINDOW_PAST = int(os.environ.get("WINDOW_PAST", "7"))
WINDOW_FUTURE = int(os.environ.get("WINDOW_FUTURE", "30"))


def http(method, url, auth=None, body=None, headers=None):
    """One-shot HTTP request; returns (status, body bytes)."""
    req = urllib.request.Request(url, method=method, data=body)
    if auth is not None:
        token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
        req.add_header("Authorization", f"Basic {token}")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as err:
        return err.code, err.read()


def unfold(text):
    """Unfold RFC 5545 folded lines."""
    out = []
    for line in text.replace("\r\n", "\n").split("\n"):
        if line[:1] in (" ", "\t") and out:
            out[-1] += line[1:]
        else:
            out.append(line)
    return out


def prop_value(block, name):
    """Value of the first property `name` in an unfolded component block."""
    for line in block:
        upper = line.upper()
        if upper.startswith(name.upper() + ":") or upper.startswith(name.upper() + ";"):
            return line.split(":", 1)[1].strip()
    return None


def ical_escape(text):
    """Escape a value for an iCalendar TEXT property."""
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def fetch_plan(config, start, end):
    """Fetch meal plan entries -> {uid: (hash, vevent lines, date)}."""
    url = (
        f"{config['mealie_url']}/api/households/mealplans"
        f"?start_date={start.isoformat()}&end_date={end.isoformat()}&perPage=-1"
    )
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {config['mealie_token']}"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.load(resp)
    events = {}
    for entry in payload.get("items", []):
        day = datetime.date.fromisoformat(entry["date"])
        name = (entry.get("recipe") or {}).get("name") or entry.get("title") or "?"
        meal = (entry.get("entryType") or "dinner").capitalize()
        uid = f"mealie-{entry['id']}@mealie-mirror"
        lines = [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTART;VALUE=DATE:{day.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{(day + datetime.timedelta(days=1)).strftime('%Y%m%d')}",
            f"SUMMARY:{ical_escape(f'{meal}: {name}')}",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]
        note = entry.get("text") or ""
        if note:
            lines.insert(-1, f"DESCRIPTION:{ical_escape(note)}")
        digest = hashlib.sha256("\n".join(lines).encode()).hexdigest()[:16]
        events[uid] = (digest, lines, day)
    return events


def wrap_event(ev_lines, digest):
    """Wrap one VEVENT into a marked VCALENDAR."""
    event = list(ev_lines)
    event.insert(-1, f"{MARKER}:{digest}")
    body = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//mealie-mirror//EN"]
    body.extend(event)
    body.append("END:VCALENDAR")
    return "\r\n".join(body) + "\r\n"


def existing_mirrored(base, auth):
    """REPORT the collection -> {uid: (href, digest, date)} for mirror-owned items."""
    report = (
        '<?xml version="1.0" encoding="utf-8" ?>'
        '<C:calendar-query xmlns:D="DAV:" '
        'xmlns:C="urn:ietf:params:xml:ns:caldav">'
        "<D:prop><C:calendar-data/></D:prop>"
        '<C:filter><C:comp-filter name="VCALENDAR">'
        '<C:comp-filter name="VEVENT"/></C:comp-filter></C:filter>'
        "</C:calendar-query>"
    )
    status, body = http(
        "REPORT",
        base,
        auth,
        report.encode(),
        {"Content-Type": "application/xml", "Depth": "1"},
    )
    if status != 207:
        raise RuntimeError(f"REPORT {base} -> {status}")
    out = {}
    namespaces = {"D": "DAV:", "C": "urn:ietf:params:xml:ns:caldav"}
    for resp in ET.fromstring(body).findall("D:response", namespaces):
        href = resp.findtext("D:href", namespaces=namespaces)
        data = resp.findtext(".//C:calendar-data", namespaces=namespaces) or ""
        lines = unfold(data)
        digest = prop_value(lines, MARKER)
        uid = prop_value(lines, "UID")
        raw_start = (prop_value(lines, "DTSTART") or "").split("T")[0]
        try:
            day = datetime.datetime.strptime(raw_start, "%Y%m%d").date()
        except ValueError:
            day = None
        if digest and uid:
            out[uid] = (href, digest, day)
    return out


def upsert_events(base, auth, events, mirrored):
    """PUT new/changed plan events; returns (created, updated, kept)."""
    created = updated = kept = 0
    for uid, (digest, event, _) in events.items():
        if uid in mirrored and mirrored[uid][1] == digest:
            kept += 1
            continue
        action = "update" if uid in mirrored else "create"
        safe = hashlib.sha256(uid.encode()).hexdigest()[:32]
        if DRY_RUN:
            print(f"DRY: {action} {uid}")
        else:
            status, _ = http(
                "PUT",
                f"{base}mealie-{safe}.ics",
                auth,
                wrap_event(event, digest).encode(),
                {"Content-Type": "text/calendar"},
            )
            if status not in (200, 201, 204):
                print(f"WARN: PUT {uid} -> {status}", file=sys.stderr)
                continue
        created += action == "create"
        updated += action == "update"
    return created, updated, kept


def delete_removed(auth, events, mirrored, start):
    """DELETE mirror-owned events dropped from the plan; returns count.

    Events dated before the sync window are kept as meal history — the
    windowed fetch can't see them, so their absence proves nothing.
    """
    deleted = 0
    for uid, (href, _, day) in mirrored.items():
        if uid in events:
            continue
        if day is not None and day < start:
            continue
        if DRY_RUN:
            print(f"DRY: delete {uid}")
        else:
            status, _ = http("DELETE", f"{RADICALE_URL}{href}", auth)
            if status not in (200, 204):
                print(f"WARN: DELETE {uid} -> {status}", file=sys.stderr)
                continue
        deleted += 1
    return deleted


def main():
    """Sync the meal plan window into the configured collection."""
    path = os.environ.get("MIRROR_CONFIG", "/config/config.json")
    with open(path, encoding="utf-8") as handle:
        config = json.load(handle)
    base = f"{RADICALE_URL}{config['collection']}"
    auth = (config["user"], config["password"])
    today = datetime.date.today()
    start = today - datetime.timedelta(days=WINDOW_PAST)
    end = today + datetime.timedelta(days=WINDOW_FUTURE)

    events = fetch_plan(config, start, end)
    mirrored = existing_mirrored(base, auth)
    created, updated, kept = upsert_events(base, auth, events, mirrored)
    deleted = delete_removed(auth, events, mirrored, start)
    print(
        f"{config['collection']}: {len(events)} planned meals | "
        f"+{created} ~{updated} -{deleted} ={kept}"
    )


if __name__ == "__main__":
    main()
