# Peace Unity Universal Phone Guardian v2

Standard-library Python. No root, no installs. Security + performance + ad-blocking checks.

## Run (Android - Termux from F-Droid)
    pkg update && pkg install python
    python guardian.py --selftest     # all PASS
    python guardian.py                # scan; saves latest-report.json and latest-report.html
    python server.py                  # dashboard at http://127.0.0.1:8765 (this device only)

## Run (Windows / macOS / Linux)
    python guardian.py     (py guardian.py on Windows, python3 on macOS/Linux)

## Options
    --offline          skip network tests (also skips the ad-block test)
    --adblock-test     test whether ads/trackers are being blocked (DNS level)
    --json   --history   --clean   --no-save   --version
    --check-url URL    offline link red-flag check (never opens the link)
    --check-text TEXT  scan a suspicious message

## Ad & tracker blocking
The test resolves 20 well-known ad/tracker names plus 3 normal sites. Names that fail or point to 0.0.0.0 count as blocked.
If the normal sites don't resolve the result is "inconclusive" (never a false 100%). The Android scan also reports whether
Private DNS is a filtering provider and lists apps allowed to draw over other apps (a common pop-up-ad trick).
To block ads: Android Settings > Network > Private DNS > dns.adguard-dns.com; Firefox + uBlock Origin or Brave; Safari content blockers on iPhone.
Limits: DNS blocking cannot stop every ad (YouTube / in-app ads), and the Guardian never changes your settings itself.

## What else it checks
Android: patch age and OS support, apps by install source (sideloaded), spy / remote-control name matches, system-name disguises,
accessibility services, notification readers, keyboards, device-admin entries, USB / wireless debugging, app verification, VPN interfaces,
battery heat/health, RAM, uptime, storage, NEW APPS since the last scan.
Desktop: listening network services, firewall, disk encryption (macOS), busiest processes, RAM, uptime, storage.

## Honest limits
Reports only what the OS lets an ordinary app see. A name match is a lead, never proof. It cannot identify a person,
prove a device is clean, or find every spyware. iPhone/iPad do not allow device scans - use Safety Check and App Privacy Report.
Reports are stored in ~/.peace_unity_phone_guardian/ with owner-only permissions. The dashboard listens on 127.0.0.1 only,
checks Host/Origin, requires a request header, and sends strict security headers.
Upload latest-report.json to the LifeHaven app (Phone Security > Phone Guardian) to view it there.
