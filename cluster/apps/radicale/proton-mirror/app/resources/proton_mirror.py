"""Mirror Proton Calendar secret ICS feeds into Radicale collections.

Proton Calendar is the household's invite intake (its iMIP handling
auto-adds emailed invitations); this job drains it into the real,
self-hosted calendar. Stateless: every event the mirror writes carries an
X-PROTON-MIRROR property with a content hash, so each run can identify
its own events, update changed ones, and delete upstream cancellations —
without ever touching events created directly in Radicale.

Config: /config/mirrors.json — [{"ics_url", "user", "password",
"collection"}, ...]; RADICALE_URL and DRY_RUN come from the environment.
"""

import base64
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
MARKER = "X-PROTON-MIRROR"


def http(method, url, user=None, password=None, body=None, headers=None):
    req = urllib.request.Request(url, method=method, data=body)
    if user is not None:
        token = base64.b64encode(f"{user}:{password}".encode()).decode()
        req.add_header("Authorization", f"Basic {token}")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def unfold(text):
    """Unfold RFC 5545 folded lines."""
    out = []
    for line in text.replace("\r\n", "\n").split("\n"):
        if line[:1] in (" ", "\t") and out:
            out[-1] += line[1:]
        else:
            out.append(line)
    return out


def extract_blocks(lines, kind):
    """Return list of BEGIN:<kind>..END:<kind> blocks (as line lists)."""
    blocks, cur, depth = [], [], 0
    for line in lines:
        if line.upper() == f"BEGIN:{kind}":
            depth += 1
        if depth > 0:
            cur.append(line)
        if line.upper() == f"END:{kind}":
            depth -= 1
            if depth == 0:
                blocks.append(cur)
                cur = []
    return blocks


def prop_value(block, name):
    for line in block:
        if line.upper().startswith(name.upper() + ":") or line.upper().startswith(
            name.upper() + ";"
        ):
            return line.split(":", 1)[1].strip()
    return None


def feed_events(ics_text):
    """Parse feed -> (timezone blocks, {uid: (hash, vevent lines)})."""
    lines = unfold(ics_text)
    tz_blocks = extract_blocks(lines, "VTIMEZONE")
    events = {}
    for ev in extract_blocks(lines, "VEVENT"):
        uid = prop_value(ev, "UID")
        if not uid:
            continue
        digest = hashlib.sha256("\n".join(ev).encode()).hexdigest()[:16]
        events[uid] = (digest, ev)
    return tz_blocks, events


def wrap_event(ev_lines, tz_blocks, digest):
    body = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//proton-mirror//EN"]
    for tz in tz_blocks:
        body.extend(tz)
    ev = list(ev_lines)
    ev.insert(-1, f"{MARKER}:{digest}")
    body.extend(ev)
    body.append("END:VCALENDAR")
    return "\r\n".join(body) + "\r\n"


def existing_mirrored(base, user, password):
    """REPORT the collection -> {uid: (href, digest)} for mirror-owned items."""
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
        user,
        password,
        report.encode(),
        {"Content-Type": "application/xml", "Depth": "1"},
    )
    if status != 207:
        raise RuntimeError(f"REPORT {base} -> {status}")
    out = {}
    ns = {"D": "DAV:", "C": "urn:ietf:params:xml:ns:caldav"}
    for resp in ET.fromstring(body).findall("D:response", ns):
        href = resp.findtext("D:href", namespaces=ns)
        data = resp.findtext(".//C:calendar-data", namespaces=ns) or ""
        lines = unfold(data)
        digest = prop_value(lines, MARKER)
        uid = prop_value(lines, "UID")
        if digest and uid:
            out[uid] = (href, digest)
    return out


def sync(mirror):
    base = f"{RADICALE_URL}{mirror['collection']}"
    user, password = mirror["user"], mirror["password"]

    status, feed = http("GET", mirror["ics_url"])
    if status != 200:
        raise RuntimeError(f"feed fetch -> {status}")
    tz_blocks, events = feed_events(feed.decode("utf-8", "replace"))
    mirrored = existing_mirrored(base, user, password)

    created = updated = deleted = kept = 0
    for uid, (digest, ev) in events.items():
        if uid in mirrored and mirrored[uid][1] == digest:
            kept += 1
            continue
        action = "update" if uid in mirrored else "create"
        safe = hashlib.sha256(uid.encode()).hexdigest()[:32]
        url = f"{base}proton-{safe}.ics"
        if DRY_RUN:
            print(f"DRY: {action} {uid}")
        else:
            s, _ = http(
                "PUT",
                url,
                user,
                password,
                wrap_event(ev, tz_blocks, digest).encode(),
                {"Content-Type": "text/calendar"},
            )
            if s not in (200, 201, 204):
                print(f"WARN: PUT {uid} -> {s}", file=sys.stderr)
                continue
        created += action == "create"
        updated += action == "update"

    for uid, (href, _) in mirrored.items():
        if uid not in events:
            if DRY_RUN:
                print(f"DRY: delete {uid}")
            else:
                s, _ = http("DELETE", f"{RADICALE_URL}{href}", user, password)
                if s not in (200, 204):
                    print(f"WARN: DELETE {uid} -> {s}", file=sys.stderr)
                    continue
            deleted += 1

    print(
        f"{mirror['collection']}: {len(events)} in feed | "
        f"+{created} ~{updated} -{deleted} ={kept}"
    )


def main():
    config = os.environ.get("MIRRORS_CONFIG", "/config/mirrors.json")
    mirrors = json.load(open(config))
    failures = 0
    for mirror in mirrors:
        try:
            sync(mirror)
        except Exception as exc:  # noqa: BLE001 - keep other mirrors running
            print(f"ERROR {mirror.get('collection')}: {exc}", file=sys.stderr)
            failures += 1
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
