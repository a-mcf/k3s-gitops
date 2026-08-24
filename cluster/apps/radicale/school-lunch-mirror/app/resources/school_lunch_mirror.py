"""Mirror the school lunch menu into a Radicale calendar.

The district publishes menus through LINQ Connect; this job projects the
lunch session onto the shared family calendar as all-day entries. Stateless
in the same way as the Mealie mirror: every event carries an
X-SCHOOL-LUNCH-MIRROR property with a content hash, so each run identifies
its own events, updates changed ones, and deletes entries that disappear
from the published menu — without touching events created directly in
Radicale.

Days absent from the API get no event, which is how closures and holidays
handle themselves: AcademicCalendars comes back empty for this district, so
absence of a menu is the only closure signal available.

Config: config.json — {"district_id", "building_id", "user", "password",
"collection"}; MIRROR_CONFIG, RADICALE_URL and DRY_RUN come from the
environment. The IDs live in the secret rather than the manifest because
together they identify which school a child attends.
"""

import base64
import datetime
import hashlib
import json
import os
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

RADICALE_URL = os.environ.get(
    "RADICALE_URL", "http://radicale.radicale.svc.cluster.local:5232"
)
MENU_API = os.environ.get("MENU_API", "https://api.linqconnect.com/api/FamilyMenu")
DRY_RUN = os.environ.get("DRY_RUN", "") == "1"
MARKER = "X-SCHOOL-LUNCH-MIRROR"
SESSION = os.environ.get("SERVING_SESSION", "Lunch")
WINDOW_PAST = int(os.environ.get("WINDOW_PAST", "3"))
WINDOW_FUTURE = int(os.environ.get("WINDOW_FUTURE", "30"))
# Categories worth naming in the event title. Everything else (milk, the
# standing fruit and vegetable bars) is noise on a calendar and lands in the
# description instead.
TITLE_CATEGORIES = ("Main Entree",)
# The upstream endpoint 403s a bare urllib User-Agent.
BROWSER_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


def http(method, url, auth=None, body=None, headers=None):
    """One-shot HTTP request; returns (status, body bytes).

    Retries connection-refused a few times: a fresh job pod's IP takes a
    moment to land in kube-router's netpol ipsets, so the first packets
    to in-cluster services can bounce.
    """
    req = urllib.request.Request(url, method=method, data=body)
    if auth is not None:
        token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
        req.add_header("Authorization", f"Basic {token}")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as err:
            return err.code, err.read()
        except urllib.error.URLError as err:
            if attempt == 3 or not isinstance(err.reason, ConnectionRefusedError):
                raise
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{method} {url}: retries exhausted")


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


def day_dishes(day):
    """One published day -> (title items, 'Category: a, b' detail lines)."""
    titles, detail = [], []
    for meal in day.get("MenuMeals") or []:
        for category in meal.get("RecipeCategories") or []:
            name = (category.get("CategoryName") or "").strip()
            items = [
                (recipe.get("RecipeName") or "").strip()
                for recipe in category.get("Recipes") or []
                if (recipe.get("RecipeName") or "").strip()
            ]
            if not items:
                continue
            if name in TITLE_CATEGORIES:
                titles.extend(items)
            detail.append(f"{name}: {', '.join(items)}")
    return titles, detail


def day_event(date, titles, detail):
    """Build the all-day VEVENT lines for one menu day."""
    summary = f"{SESSION}: " + (" / ".join(titles[:3]) if titles else "see description")
    next_day = (date + datetime.timedelta(days=1)).strftime("%Y%m%d")
    lines = [
        "BEGIN:VEVENT",
        f"UID:lunch-{date.strftime('%Y%m%d')}@school-lunch-mirror",
        f"DTSTART;VALUE=DATE:{date.strftime('%Y%m%d')}",
        f"DTEND;VALUE=DATE:{next_day}",
        f"SUMMARY:{ical_escape(summary)}",
        "TRANSP:TRANSPARENT",
        "END:VEVENT",
    ]
    if detail:
        lines.insert(-1, f"DESCRIPTION:{ical_escape(chr(10).join(detail))}")
    return lines


def published_days(payload):
    """Yield (date, day) for every day of the configured serving session."""
    for session in payload.get("FamilyMenuSessions") or []:
        if (session.get("ServingSession") or "").strip() != SESSION:
            continue
        for plan in session.get("MenuPlans") or []:
            for day in plan.get("Days") or []:
                raw = day.get("Date")
                if raw:
                    yield datetime.datetime.strptime(raw, "%m/%d/%Y").date(), day


def fetch_menu(config, start, end):
    """Fetch the published menu -> {uid: (hash, vevent lines, date)}."""
    url = (
        f"{MENU_API}?buildingId={config['building_id']}"
        f"&districtId={config['district_id']}"
        f"&startDate={start.strftime('%-m-%-d-%Y')}"
        f"&endDate={end.strftime('%-m-%-d-%Y')}"
    )
    status, body = http("GET", url, headers={"User-Agent": BROWSER_UA})
    if status != 200:
        raise RuntimeError(f"menu fetch -> {status}")

    events = {}
    for date, day in published_days(json.loads(body)):
        titles, detail = day_dishes(day)
        if not titles and not detail:
            continue
        lines = day_event(date, titles, detail)
        digest = hashlib.sha256("\n".join(lines).encode()).hexdigest()[:16]
        events[prop_value(lines, "UID")] = (digest, lines, date)
    return events


def wrap_event(ev_lines, digest):
    """Wrap one VEVENT into a marked VCALENDAR."""
    event = list(ev_lines)
    event.insert(-1, f"{MARKER}:{digest}")
    body = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//school-lunch-mirror//EN"]
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
    """PUT new/changed menu events; returns (created, updated, kept)."""
    created = updated = kept = 0
    for uid, (digest, event, _) in events.items():
        if uid in mirrored and mirrored[uid][1] == digest:
            kept += 1
            continue
        action = "update" if uid in mirrored else "create"
        safe = hashlib.sha256(uid.encode()).hexdigest()[:32]
        if DRY_RUN:
            print(f"DRY: {action} {uid} :: {prop_value(event, 'SUMMARY')}")
        else:
            status, _ = http(
                "PUT",
                f"{base}lunch-{safe}.ics",
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
    """DELETE mirror-owned events dropped from the menu; returns count.

    Events dated before the sync window are kept — the windowed fetch can't
    see them, so their absence proves nothing.
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
    """Sync the published menu window into the configured collection."""
    path = os.environ.get("MIRROR_CONFIG", "/config/config.json")
    with open(path, encoding="utf-8") as handle:
        config = json.load(handle)
    base = f"{RADICALE_URL}{config['collection']}"
    auth = (config["user"], config["password"])
    today = datetime.date.today()
    start = today - datetime.timedelta(days=WINDOW_PAST)
    end = today + datetime.timedelta(days=WINDOW_FUTURE)

    events = fetch_menu(config, start, end)
    mirrored = existing_mirrored(base, auth)
    created, updated, kept = upsert_events(base, auth, events, mirrored)
    deleted = delete_removed(auth, events, mirrored, start)
    print(
        f"{config['collection']}: {len(events)} menu days | "
        f"+{created} ~{updated} -{deleted} ={kept}"
    )


if __name__ == "__main__":
    main()
