"""Mirror Proton Calendar secret ICS feeds into Radicale collections.

Proton Calendar is the household's invite intake (its iMIP handling
auto-adds emailed invitations); this job drains it into the real,
self-hosted calendar. Stateless: every event the mirror writes carries an
X-PROTON-MIRROR property with a content hash, so each run can identify
its own events, update changed ones, and delete upstream cancellations —
without ever touching events created directly in Radicale.

Config: mirrors.json — [{"ics_url", "user", "password", "collection"},
...]; MIRRORS_CONFIG, RADICALE_URL and DRY_RUN come from the environment.
"""

import base64
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
DRY_RUN = os.environ.get("DRY_RUN", "") == "1"
MARKER = "X-PROTON-MIRROR"


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
    """Value of the first property `name` in an unfolded component block."""
    for line in block:
        upper = line.upper()
        if upper.startswith(name.upper() + ":") or upper.startswith(name.upper() + ";"):
            return line.split(":", 1)[1].strip()
    return None


def feed_events(ics_text):
    """Parse feed -> (timezone blocks, {uid: (hash, vevent lines)})."""
    lines = unfold(ics_text)
    tz_blocks = extract_blocks(lines, "VTIMEZONE")
    events = {}
    for event in extract_blocks(lines, "VEVENT"):
        uid = prop_value(event, "UID")
        if not uid:
            continue
        digest = hashlib.sha256("\n".join(event).encode()).hexdigest()[:16]
        events[uid] = (digest, event)
    return tz_blocks, events


def wrap_event(ev_lines, tz_blocks, digest):
    """Wrap one VEVENT (plus feed timezones) into a marked VCALENDAR."""
    body = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//proton-mirror//EN"]
    for timezone in tz_blocks:
        body.extend(timezone)
    event = list(ev_lines)
    event.insert(-1, f"{MARKER}:{digest}")
    body.extend(event)
    body.append("END:VCALENDAR")
    return "\r\n".join(body) + "\r\n"


def existing_mirrored(base, auth):
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
        if digest and uid:
            out[uid] = (href, digest)
    return out


def upsert_events(base, auth, events, mirrored, tz_blocks):
    """PUT new/changed feed events; returns (created, updated, kept)."""
    created = updated = kept = 0
    for uid, (digest, event) in events.items():
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
                f"{base}proton-{safe}.ics",
                auth,
                wrap_event(event, tz_blocks, digest).encode(),
                {"Content-Type": "text/calendar"},
            )
            if status not in (200, 201, 204):
                print(f"WARN: PUT {uid} -> {status}", file=sys.stderr)
                continue
        created += action == "create"
        updated += action == "update"
    return created, updated, kept


def delete_cancelled(auth, events, mirrored):
    """DELETE mirror-owned events that left the feed; returns count."""
    deleted = 0
    for uid, (href, _) in mirrored.items():
        if uid in events:
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


def sync(mirror):
    """Sync one feed -> collection pair."""
    base = f"{RADICALE_URL}{mirror['collection']}"
    auth = (mirror["user"], mirror["password"])

    status, feed = http("GET", mirror["ics_url"])
    if status != 200:
        raise RuntimeError(f"feed fetch -> {status}")
    tz_blocks, events = feed_events(feed.decode("utf-8", "replace"))
    mirrored = existing_mirrored(base, auth)

    created, updated, kept = upsert_events(base, auth, events, mirrored, tz_blocks)
    deleted = delete_cancelled(auth, events, mirrored)
    print(
        f"{mirror['collection']}: {len(events)} in feed | "
        f"+{created} ~{updated} -{deleted} ={kept}"
    )


def main():
    """Run every configured mirror; exit nonzero if any failed."""
    config = os.environ.get("MIRRORS_CONFIG", "/config/mirrors.json")
    with open(config, encoding="utf-8") as handle:
        mirrors = json.load(handle)
    failures = 0
    for mirror in mirrors:
        try:
            sync(mirror)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"ERROR {mirror.get('collection')}: {exc}", file=sys.stderr)
            failures += 1
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
