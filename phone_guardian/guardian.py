#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Peace Unity Universal Phone Guardian  v2
Local-first security + performance diagnostics. Standard library only. No root needed.

Honest scope: it reports what the operating system lets an ordinary app see. It cannot prove a device is
clean, identify a person behind an address, or detect every spyware/malware. Nothing is changed automatically.
"""
from __future__ import annotations
import argparse, hashlib, html, json, os, platform, re, shutil, socket, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, unquote

APP = "Peace Unity Universal Phone Guardian"
VERSION = "2.0.0"
BASE = Path(os.environ.get("GUARDIAN_HOME") or (Path.home() / ".peace_unity_phone_guardian"))
REPORTS, CACHE = BASE / "reports", BASE / "cache"
MAX_REPORTS = 30
LEVEL_WEIGHT = {"critical": 25, "warning": 12, "review": 5, "info": 0, "limited": 0}

# ───────────────────────── helpers ─────────────────────────
def command(args, timeout=12):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout, errors="replace")
        return p.stdout.strip(), p.stderr.strip(), p.returncode
    except subprocess.TimeoutExpired:
        return "", "timed out", 124
    except (FileNotFoundError, PermissionError, OSError) as e:
        return "", str(e), 127
    except Exception as e:                      # never let one check crash the scan
        return "", str(e), 1

def read_text(path, limit=200_000):
    try:
        return Path(path).read_text(errors="replace")[:limit]
    except Exception:
        return ""

def getprop(key):
    out, _, rc = command(["getprop", key])
    return out if rc == 0 else ""

def setting(ns, key):
    out, _, rc = command(["settings", "get", ns, key])
    if rc != 0 or not out or out.lower() == "null":
        return None
    return out

def detect_platform():
    if os.environ.get("ANDROID_ROOT") or "android" in platform.platform().lower() or Path("/system/build.prop").exists():
        return "android"
    return {"darwin": "macos", "windows": "windows", "linux": "linux"}.get(platform.system().lower(), platform.system().lower())

def add(items, level, title, detail, action="", category="general"):
    items.append({"level": level, "category": category, "title": title, "detail": str(detail), "action": action})

def tokens(name):
    return [t for t in re.split(r"[^a-z0-9]+", name.lower()) if t]

# ───────────────────────── signature lists (name hints only, never proof) ─────────────────────────
STALKERWARE = ("flexispy", "cocospy", "spyzie", "spyic", "xnspy", "hoverwatch", "eyezy", "umobix", "spyera", "kidsguard",
               "truthspy", "webwatcher", "mobistealth", "spyine", "spyhuman", "pctattletale", "phonesheriff", "ikeymonitor",
               "mobilespy", "spyfone", "cellspy", "keylogger", "stalkerware", "spyware", "spyapp")
STALKERWARE_EXACT = {"mspy", "tispy", "spy", "stalker", "keylog"}
REMOTE_TOOLS = ("anydesk", "teamviewer", "rustdesk", "airdroid", "splashtop", "remotix", "vnc")
STORE_INSTALLERS = {"com.android.vending", "com.sec.android.app.samsungapps", "com.amazon.venezia", "com.huawei.appmarket",
                    "com.xiaomi.mipicks", "com.heytap.market", "com.oppo.market", "com.vivo.appstore", "org.fdroid.fdroid"}

# ───────────────────────── URL / TEXT scanners ─────────────────────────
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "cutt.ly", "rb.gy", "buff.ly", "shorturl.at", "tiny.cc", "rebrand.ly"}
RISKY_TLDS = {"zip", "mov", "top", "xyz", "click", "tk", "gq", "cf", "ml", "ga", "country", "support", "work", "rest", "icu", "cam"}
BRANDS = {"paypal": ("paypal.com",), "apple": ("apple.com", "icloud.com"), "icloud": ("icloud.com", "apple.com"), "amazon": ("amazon.com", "amazon.co.uk", "amazon.ca"),
          "microsoft": ("microsoft.com", "live.com", "office.com", "outlook.com"), "google": ("google.com", "gmail.com"),
          "netflix": ("netflix.com",), "usps": ("usps.com",), "fedex": ("fedex.com",), "irs": ("irs.gov",), "medicare": ("medicare.gov", "cms.gov"),
          "chase": ("chase.com",), "wellsfargo": ("wellsfargo.com",), "bankofamerica": ("bankofamerica.com",), "facebook": ("facebook.com", "fb.com", "meta.com"),
          "instagram": ("instagram.com",), "whatsapp": ("whatsapp.com",), "dhl": ("dhl.com",), "coinbase": ("coinbase.com",), "binance": ("binance.com",)}
LURE_WORDS = ("login", "signin", "verify", "secure", "update", "account", "wallet", "suspended", "confirm", "billing", "unlock", "refund")
SECOND_LEVELS = {"co", "com", "org", "gov", "ac", "net", "edu"}

def registrable(host):
    parts = host.split(".")
    if len(parts) >= 3 and len(parts[-1]) == 2 and parts[-2] in SECOND_LEVELS:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:]) if len(parts) >= 2 else host

def scan_url(value):
    raw = (value or "").strip()
    if not raw:
        return {"input": raw, "hostname": "", "verdict": "not_checked", "score": 0, "reasons": ["No URL supplied."], "network_access": "none"}
    cand = raw if "://" in raw else "https://" + raw
    reasons, score = [], 0
    try:
        u = urlparse(cand)
        host = (u.hostname or "").lower().rstrip(".")
    except ValueError:
        u, host = None, ""
    if not host or u is None:
        return {"input": raw[:300], "hostname": "", "verdict": "review", "score": 3, "reasons": ["Could not read a valid hostname."], "network_access": "none"}
    def hit(points, msg):
        nonlocal score
        score += points; reasons.append(msg)
    if u.scheme not in ("http", "https"): hit(3, f"Unusual scheme '{u.scheme}'.")
    if u.scheme == "http": hit(1, "Not encrypted (http).")
    if u.username or u.password: hit(4, "Contains embedded login info before the real host (a classic disguise).")
    if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host): hit(4, "Uses a raw IP address instead of a name.")
    elif re.fullmatch(r"\d+|0x[0-9a-f]+", host): hit(4, "Numeric-obfuscated IP address.")
    if host.startswith("xn--") or ".xn--" in host:
        try: shown = host.encode("ascii").decode("idna")
        except Exception: shown = host
        hit(3, f"Look-alike (punycode) characters — it decodes to '{shown}'.")
    if any(ord(c) > 127 for c in host): hit(3, "Non-English look-alike characters in the name.")
    if host in SHORTENERS: hit(3, "Shortened link hides the real destination.")
    tld = host.rsplit(".", 1)[-1]
    if tld in RISKY_TLDS: hit(2, f"'.{tld}' endings are frequently abused.")
    if host.count(".") >= 4: hit(2, "Very many sub-domain parts.")
    if host.count("-") >= 3: hit(1, "Several hyphens in the name.")
    if len(host) > 60: hit(1, "Unusually long hostname.")
    if len(raw) > 120: hit(1, "Very long link.")
    if len(re.findall(r"%[0-9a-fA-F]{2}", raw)) >= 5: hit(1, "Heavily percent-encoded.")
    reg = registrable(host)
    toks = set(tokens(host.replace(".", "-")))
    for brand, official in BRANDS.items():
        if brand in toks or any(brand in t for t in toks if len(brand) >= 6):
            if reg not in official:
                hit(4, f"Mentions '{brand}' but is not the official site ({official[0]}).")
                break
    lure = [w for w in LURE_WORDS if w in (host + unquote(u.path or "")).lower()]
    if lure: hit(min(2, len(lure)), "Urgent/account words in the address: " + ", ".join(lure[:4]) + ".")
    verdict = "high_risk" if score >= 6 else "medium_risk" if score >= 3 else "low_flags" if score >= 1 else "no_flags"
    if not reasons: reasons.append("No simple red flags found. This does NOT prove the site is safe.")
    return {"input": raw[:300], "hostname": host, "verdict": verdict, "score": score, "reasons": reasons,
            "network_access": "none — offline pattern check; the link was never opened"}

SCAM_WORDS = ("urgent", "immediately", "act now", "final notice", "verify your", "account suspended", "account locked", "gift card",
              "wire transfer", "bitcoin", "crypto", "social security", "medicare", "irs", "refund", "you have won", "winner",
              "one-time code", "otp", "verification code", "password", "do not tell", "keep this secret", "arrest", "warrant",
              "grandson", "grandchild", "bail", "package could not be delivered", "customs fee", "tax refund")

def scan_text(text):
    t = (text or "").lower()
    reasons, score = [], 0
    hits = [w for w in SCAM_WORDS if w in t]
    if hits: score += min(4, len(hits)); reasons.append("Pressure/scam wording: " + ", ".join(hits[:8]) + ".")
    if re.search(r"\b\d{4,8}\b", t) and re.search(r"code|otp|pin", t):
        score += 2; reasons.append("Mentions a numeric code — never read codes to anyone who contacts you.")
    urls = re.findall(r"(?:https?://|www\.)[^\s<>\"']+", text or "", flags=re.I)
    results = [scan_url(u) for u in urls[:10]]
    for r in results:
        if r["verdict"] in ("medium_risk", "high_risk"): score += 3; reasons.append(f"Link {r['hostname']}: " + "; ".join(r["reasons"][:2]))
    verdict = "high_risk" if score >= 6 else "medium_risk" if score >= 3 else "low_flags" if score >= 1 else "no_flags"
    if not reasons: reasons.append("No obvious scam wording or link red flags. Scams can look clean; verify by calling the number on the official site or card.")
    return {"verdict": verdict, "score": score, "reasons": reasons, "links": results}

# ───────────────────────── ad & tracker blocking test ─────────────────────────
AD_TEST_DOMAINS = ("doubleclick.net", "googleads.g.doubleclick.net", "pagead2.googlesyndication.com", "securepubads.g.doubleclick.net",
                   "adservice.google.com", "ib.adnxs.com", "trc.taboola.com", "widgets.outbrain.com", "c.amazon-adsystem.com",
                   "static.criteo.net", "ads.pubmatic.com", "rtb.openx.net", "ads.mopub.com", "unityads.unity3d.com", "applovin.com",
                   "www.google-analytics.com", "app-measurement.com", "sb.scorecardresearch.com", "static.hotjar.com", "connect.facebook.net")
CONTROL_DOMAINS = ("example.com", "wikipedia.org", "www.gstatic.com")
AD_DNS_HINTS = ("adguard", "nextdns", "controld", "adblock.dns.mullvad", "blokada", "ahadns", "dnsforge", "oisd")
NULL_IPS = ("0.0.0.0", "::", "127.0.0.1", "::1")

def _resolve_state(host):
    """'blocked' if the name fails or points to a null address, 'reached' if it resolves normally."""
    try:
        infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
    except OSError:
        return "blocked"
    addrs = {i[4][0] for i in infos}
    return "blocked" if addrs and all(a in NULL_IPS or a.startswith("127.") for a in addrs) else "reached"

def adblock_test():
    from concurrent.futures import ThreadPoolExecutor, as_completed
    names = list(CONTROL_DOMAINS) + list(AD_TEST_DOMAINS)
    states = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(_resolve_state, h): h for h in names}
        try:
            for fu in as_completed(futs, timeout=20):
                states[futs[fu]] = fu.result()
        except Exception:
            pass
    control_ok = sum(1 for h in CONTROL_DOMAINS if states.get(h) == "reached") >= 2
    details = [{"domain": h, "state": states.get(h, "timeout")} for h in AD_TEST_DOMAINS]
    blocked = sum(1 for d in details if d["state"] in ("blocked", "timeout"))
    pct = round(blocked / len(details) * 100)
    if not control_ok: status = "inconclusive"
    elif pct >= 70: status = "strong"
    elif pct >= 10: status = "partial"
    else: status = "none"
    return {"status": status, "blocked": blocked, "total": len(details), "percent": pct, "control_ok": control_ok, "details": details,
            "note": "DNS-level test. It shows whether this network/device resolves well-known ad and tracker names. In-app and first-party ads (e.g. YouTube) usually cannot be blocked this way."}

def ad_findings(f, info, res=None):
    r = res or adblock_test()
    info["adblock"] = {k: r[k] for k in ("status", "blocked", "total", "percent")}
    msg = {"strong": ("info", f"Ad & tracker blocking is working: {r['blocked']} of {r['total']} test domains were blocked.", ""),
           "partial": ("info", f"Partial blocking: {r['blocked']} of {r['total']} test domains were blocked.", "Use a stronger filtering DNS (e.g. AdGuard DNS) or add a blocker to your browser for the rest."),
           "none": ("review", f"No ad/tracker blocking detected: 0-{r['percent']}% of test domains blocked.", "Turn on a filtering Private DNS (Android: Settings → Network → Private DNS → dns.adguard-dns.com) or install a reputable blocker."),
           "inconclusive": ("limited", "Ad-blocking test could not run (no working connection to the control sites).", "Connect to the internet and run again.")}[r["status"]]
    add(f, msg[0], "Ad & tracker blocking", msg[1], msg[2], "ads")
    return r

# ───────────────────────── performance (any Linux-like / Android) ─────────────────────────
def perf_checks(f, info):
    mem = read_text("/proc/meminfo")
    if mem:
        def kb(k):
            m = re.search(rf"^{k}:\s+(\d+)", mem, re.M); return int(m.group(1)) if m else None
        total, avail = kb("MemTotal"), kb("MemAvailable")
        if total and avail:
            pct = round(avail / total * 100, 1)
            info["ram_total_gb"], info["ram_available_percent"] = round(total / 1048576, 2), pct
            lvl = "warning" if pct < 10 else "review" if pct < 20 else "info"
            add(f, lvl, "Memory (RAM)", f"{pct}% free of {round(total/1048576,1)} GB.",
                "Restart the phone, update apps, and remove apps you don't use." if lvl != "info" else "", "performance")
    load = read_text("/proc/loadavg").split()
    if load:
        info["load_average"] = load[:3]
        add(f, "info", "CPU load average", " / ".join(load[:3]), "Sustained values far above the number of CPU cores mean heavy background work.", "performance")
    up = read_text("/proc/uptime").split()
    if up:
        days = float(up[0]) / 86400
        info["uptime_days"] = round(days, 1)
        lvl = "review" if days > 14 else "info"
        add(f, lvl, "Time since last restart", f"{days:.1f} days.", "A restart every week or so clears stuck processes and applies pending updates." if lvl == "review" else "", "performance")

def storage_checks(f, info):
    try:
        u = shutil.disk_usage(Path.home())
        pct = round(u.used / u.total * 100, 1) if u.total else 0
        free = round(u.free / 1024**3, 2)
        info["storage_used_percent"], info["storage_free_gb"] = pct, free
        lvl = "warning" if pct >= 95 else "review" if pct >= 85 else "info"
        add(f, lvl, "Storage", f"{pct}% used; {free} GB free.",
            "Back up photos first, then clear big videos, downloads and unused apps. Under ~10% free, phones slow down and can't update." if lvl != "info" else "", "performance")
    except OSError as e:
        add(f, "limited", "Storage check unavailable", e, "", "performance")

# ───────────────────────── Android ─────────────────────────
def android_checks(f, info):
    info["manufacturer"] = getprop("ro.product.manufacturer") or "n/a"
    info["device_model"] = getprop("ro.product.model") or "n/a"
    info["android_version"] = getprop("ro.build.version.release") or platform.release()
    info["security_patch"] = getprop("ro.build.version.security_patch") or "n/a"
    try:
        major = int(re.match(r"\d+", info["android_version"]).group(0))
    except Exception:
        major = None
    if major is not None and major <= 11:
        add(f, "warning", "Android version no longer supported", f"Android {info['android_version']}.",
            "Android 11 and older no longer get Google security fixes. Use a newer phone/OS for banking and sensitive accounts.", "os")
    elif major is not None and major <= 13:
        add(f, "review", "Check your phone still gets updates", f"Android {info['android_version']}.",
            "Look up your model's update policy; vendors stop security patches after a few years.", "os")
    sp = info["security_patch"]
    try:
        age = (datetime.now() - datetime.strptime(sp, "%Y-%m-%d")).days
        lvl = "warning" if age > 365 else "review" if age > 180 else "info"
        add(f, lvl, "Security patch level", f"{sp} ({age} days old).",
            "Settings → System → Software update. A patch over 6 months old means known flaws may be unfixed." if lvl != "info" else "", "os")
    except Exception:
        add(f, "limited", "Security patch level", "Could not read it from this environment.", "Settings → About phone → Android security update.", "os")

    out, err, rc = command(["pm", "list", "packages", "-3", "-i"], 25)
    pkgs, sideloaded = {}, []
    if rc == 0 and out:
        for m in re.finditer(r"package:([A-Za-z0-9._]+)(?:\s+installer=(\S+))?", out):
            pkgs[m.group(1)] = m.group(2) or "unknown"
    else:
        out, err, rc = command(["pm", "list", "packages", "-3"], 25)
        if rc == 0:
            pkgs = {p: "unknown" for p in re.findall(r"package:([A-Za-z0-9._]+)", out)}
    if pkgs:
        info["third_party_packages"] = sorted(pkgs)
        info["third_party_package_count"] = len(pkgs)
        sideloaded = sorted(p for p, ins in pkgs.items() if ins not in STORE_INSTALLERS and ins != "unknown")
        add(f, "info", "Installed third-party apps", f"{len(pkgs)} apps. A package name alone can't prove safe or unsafe.",
            "Settings → Apps → See all apps; check developer and install source before removing anything.", "apps")
        if sideloaded:
            info["sideloaded_packages"] = sideloaded
            add(f, "review", "Apps not installed from a known app store", "\n".join(sideloaded[:40]) + (f"\n… and {len(sideloaded)-40} more" if len(sideloaded) > 40 else ""),
                "Installed from files/ADB/other sources. Confirm you installed each one yourself; remove any you don't recognize.", "apps")
        for p in pkgs:
            tk, joined = set(tokens(p)), p.lower()
            if tk & STALKERWARE_EXACT or any(s in joined for s in STALKERWARE):
                add(f, "warning", "Name matches known spy/monitoring app families", p,
                    "Open Settings → Apps → this app → check permissions and install source. A name match is a lead, not proof.", "apps")
            if any(r in joined for r in REMOTE_TOOLS):
                add(f, "review", "Remote-control app installed", p, "Legitimate if you installed it. If not, someone may have remote access: remove it and change passwords.", "apps")
            if p.startswith(("com.android.", "com.google.android.", "android.")):
                add(f, "review", "Third-party app using a system-style name (possible disguise)", p,
                    "Real system apps are not listed as user-installed. Check who made it before keeping it.", "apps")
    else:
        info["third_party_package_count"] = None
        add(f, "limited", "App inventory unavailable", (err or "No data returned")[:300],
            "Termux often can't read the package list. Review Settings → Apps → See all apps by hand.", "apps")

    acc = setting("secure", "enabled_accessibility_services")
    if acc:
        items = [x for x in acc.split(":") if x]
        info["accessibility_services"] = items
        add(f, "review", "Accessibility services turned on", "\n".join(items)[:1200],
            "These can read the screen and tap for you. Keep only services you use (screen readers etc.). Settings → Accessibility.", "permissions")
    else:
        add(f, "info", "Accessibility services", "None reported.", "", "permissions")
    nl = setting("secure", "enabled_notification_listeners")
    if nl:
        items = [x for x in nl.split(":") if x]
        info["notification_listeners"] = items
        add(f, "review", "Apps that can read your notifications", "\n".join(items)[:1200],
            "They can see codes and messages. Settings → Notifications → Device & app notifications.", "permissions")
    ime = setting("secure", "enabled_input_methods")
    if ime:
        items = [x for x in ime.split(":") if x]
        info["keyboards"] = items
        add(f, "info", "Keyboards enabled", "\n".join(items)[:800], "Third-party keyboards can see what you type; keep only ones you trust.", "permissions")
    out, err, rc = command(["dumpsys", "device_policy"], 15)
    if rc == 0 and out:
        lines = [x.strip() for x in out.splitlines() if re.search(r"(device owner|profile owner|active admin)", x, re.I)]
        if lines:
            add(f, "review", "Device administrator / owner entries", "\n".join(lines[:12])[:1000],
                "Work/school management is legitimate. If you don't have either, review Settings → Security → Device admin apps.", "permissions")
    adb = setting("global", "adb_enabled")
    adbw = setting("global", "adb_wifi_enabled")
    if adbw == "1":
        add(f, "warning", "Wireless debugging is ON", "Another computer on your Wi-Fi may be able to control the phone.", "Settings → Developer options → turn off Wireless debugging.", "settings")
    elif adb == "1":
        add(f, "review", "USB debugging is ON", "Needed only for developers.", "Settings → Developer options → turn off USB debugging if you don't use it.", "settings")
    ver = setting("global", "package_verifier_enable")
    if ver == "0":
        add(f, "warning", "App verification is OFF", "Play Protect style scanning of installs appears disabled.", "Play Store → profile → Play Protect → turn on scanning.", "settings")
    mode, host = setting("global", "private_dns_mode"), setting("global", "private_dns_specifier")
    if mode:
        info["private_dns_mode"], info["private_dns_hostname"] = mode, host or ""
        filt = bool(host) and any(h in host.lower() for h in AD_DNS_HINTS)
        add(f, "info", "Private DNS", f"Mode: {mode}; provider: {host or '—'}" + ("  → looks like an ad/tracker-filtering provider" if filt else ""),
            "" if filt else "Optional: set Private DNS to a filtering provider such as dns.adguard-dns.com to block many ads and trackers system-wide.", "ads")
    out, err, rc = command(["cmd", "appops", "query-op", "SYSTEM_ALERT_WINDOW", "allow"], 15)
    if rc == 0 and out and pkgs:
        over = sorted({p for p in re.findall(r"[A-Za-z][\w]*(?:\.[\w]+)+", out) if p in pkgs})
        if over:
            info["overlay_apps"] = over
            add(f, "review", "Apps allowed to draw over other apps", "\n".join(over[:40]),
                "Pop-up ads on top of other apps usually come from here. Settings → Apps → Special app access → Display over other apps: turn off any you don't need.", "ads")
    nd = read_text("/proc/net/dev")
    vpn = sorted(set(re.findall(r"^\s*((?:tun|tap|ppp|wg|ipsec)\w*):", nd, re.M)))
    if vpn:
        info["vpn_interfaces"] = vpn
        add(f, "info", "A VPN-style network interface is active", ", ".join(vpn), "Fine if you turned on a VPN. If not, check Settings → Network → VPN.", "network")
    out, err, rc = command(["dumpsys", "battery"])
    if rc == 0 and out:
        lv = re.search(r"level:\s*(\d+)", out); tp = re.search(r"temperature:\s*(\d+)", out); hl = re.search(r"health:\s*(\d+)", out)
        if lv: info["battery_percent"] = int(lv.group(1)); add(f, "info", "Battery level", f"{lv.group(1)}%", "", "performance")
        if tp:
            c = int(tp.group(1)) / 10; info["battery_temp_c"] = c
            lvl = "warning" if c >= 45 else "review" if c >= 40 else "info"
            add(f, lvl, "Battery temperature", f"{c:.1f} °C", "Unplug, remove the case, stop heavy apps, and let it cool. Hot batteries age faster." if lvl != "info" else "", "performance")
        if hl and hl.group(1) not in ("2", "1"):
            add(f, "warning", "Battery health reported as not good", f"health code {hl.group(1)}", "Have the battery checked or replaced.", "performance")

# ───────────────────────── Desktop (Linux / macOS / Windows) ─────────────────────────
def desktop_checks(f, info, plat):
    ports = []
    if plat == "linux":
        out, _, rc = command(["ss", "-tulnH"])
        for ln in out.splitlines():
            p = ln.split()
            if len(p) >= 5: ports.append(p[4])
    elif plat == "macos":
        out, _, rc = command(["lsof", "-iTCP", "-sTCP:LISTEN", "-nP"], 15)
        for ln in out.splitlines()[1:]:
            m = re.search(r"(\S+:\d+)\s+\(LISTEN\)", ln)
            if m: ports.append(m.group(1))
    elif plat == "windows":
        out, _, rc = command(["netstat", "-an", "-p", "tcp"], 15)
        for ln in out.splitlines():
            if "LISTENING" in ln.upper():
                p = ln.split()
                if len(p) >= 2: ports.append(p[1])
    if ports:
        wide = sorted({p for p in ports if p.startswith(("0.0.0.0:", "*:", "[::]:", ":::"))})
        info["listening_ports"] = sorted(set(ports))[:100]
        lvl = "review" if len(wide) > 8 else "info"
        add(f, lvl, "Network services listening", f"{len(set(ports))} listening; {len(wide)} open to the whole network:\n" + "\n".join(wide[:25]),
            "Services bound to all addresses can be reached by other devices. Close ones you don't use." if wide else "", "network")
    if plat == "linux":
        out, _, rc = command(["sh", "-c", "ufw status 2>/dev/null | head -1"])
        if out: add(f, "info" if "active" in out.lower() else "review", "Firewall (ufw)", out, "Enable with: sudo ufw enable" if "inactive" in out.lower() else "", "network")
    elif plat == "macos":
        out, _, rc = command(["/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"])
        if out: add(f, "info" if "enabled" in out.lower() else "review", "macOS firewall", out, "System Settings → Network → Firewall." if "disabled" in out.lower() else "", "network")
        out, _, rc = command(["fdesetup", "status"])
        if out: add(f, "info" if "On" in out else "review", "Disk encryption (FileVault)", out, "Turn on FileVault in System Settings → Privacy & Security." if "Off" in out else "", "os")
    elif plat == "windows":
        out, _, rc = command(["netsh", "advfirewall", "show", "allprofiles", "state"])
        if out: add(f, "review" if re.search(r"OFF", out, re.I) else "info", "Windows Firewall", out[:400], "Windows Security → Firewall & network protection.", "network")
    if plat != "windows":
        out, _, rc = command(["sh", "-c", "ps -eo pcpu,pmem,comm --sort=-pcpu 2>/dev/null | head -6 || ps aux | head -6"])
        if out: add(f, "info", "Busiest processes", out, "", "performance")

def network_checks(f, info):
    t0 = time.time()
    try:
        socket.getaddrinfo("example.com", 443); ms = round((time.time() - t0) * 1000)
        info["dns_lookup_ms"] = ms
        add(f, "warning" if ms > 1500 else "review" if ms > 500 else "info", "DNS lookup speed", f"{ms} ms for a public name.", "Slow DNS makes everything feel slow. Try another network or DNS." if ms > 500 else "", "network")
    except OSError:
        add(f, "warning", "Name lookup failed", "Could not resolve a public domain.", "Check Wi-Fi/data, Private DNS or filtering settings.", "network"); return
    lat = []
    for host in ("1.1.1.1", "8.8.8.8"):
        try:
            s = time.time(); socket.create_connection((host, 443), timeout=3).close(); lat.append(round((time.time() - s) * 1000))
        except OSError: pass
    if lat:
        info["tcp_latency_ms"] = lat
        m = min(lat)
        add(f, "review" if m > 300 else "info", "Connection latency", f"{m} ms to a public server.", "High latency: move closer to the router or try mobile data." if m > 300 else "", "network")

# ───────────────────────── scan orchestration ─────────────────────────
def load_latest():
    try:
        return json.loads((REPORTS / "latest-report.json").read_text())
    except Exception:
        return None

def run_scan(offline=False):
    f, plat = [], detect_platform()
    info = {"product": APP, "version": VERSION, "timestamp_utc": datetime.now(timezone.utc).isoformat(), "platform": plat,
            "os": platform.platform(), "release": platform.release(), "machine": platform.machine(), "python": platform.python_version()}
    prev = load_latest()
    checks = [(android_checks, (f, info)) if plat == "android" else (desktop_checks, (f, info, plat)),
              (perf_checks, (f, info)), (storage_checks, (f, info))]
    if not offline:
        checks.append((network_checks, (f, info)))
        checks.append((ad_findings, (f, info)))
    for fn, args in checks:
        try: fn(*args)
        except Exception as e: add(f, "limited", f"{fn.__name__} could not finish", str(e)[:300], "", "general")
    if plat == "android" and prev and prev.get("device", {}).get("third_party_packages") and info.get("third_party_packages"):
        old, new = set(prev["device"]["third_party_packages"]), set(info["third_party_packages"])
        if new - old: add(f, "review", "New apps since your last scan", "\n".join(sorted(new - old)[:40]),
                          "If you didn't install these, treat them as suspicious: check permissions, then remove.", "apps")
        if old - new: add(f, "info", "Apps removed since your last scan", "\n".join(sorted(old - new)[:40]), "", "apps")
    add(f, "info", "Scope & limits", "This scan can't identify a person, prove a device is clean, or detect every malware/stalkerware. iPhone/iPad don't allow this kind of scan.",
        "Use official stores, OS updates, Google Play Protect / Apple Safety Check, and account security pages.", "general")
    risk = sum(LEVEL_WEIGHT.get(x["level"], 0) for x in f)
    score = max(0, 100 - risk)
    grade = "Good" if score >= 85 else "Fair" if score >= 65 else "Needs attention" if score >= 40 else "High concern"
    counts = {}
    for x in f: counts[x["level"]] = counts.get(x["level"], 0) + 1
    return {"device": info, "score": score, "grade": grade, "counts": counts, "findings": f}

def render_html(data):
    e = html.escape
    rows = "".join(f'<div class="f {e(x["level"])}"><b>[{e(x["level"].upper())}] {e(x["title"])}</b><pre>{e(x["detail"])}</pre>'
                   + (f'<p><i>Next step:</i> {e(x["action"])}</p>' if x.get("action") else "") + "</div>" for x in data["findings"])
    return (f'<!doctype html><meta charset="utf-8"><title>{e(APP)} report</title><style>body{{font:16px system-ui;max-width:760px;margin:20px auto;padding:0 14px;background:#0b1715;color:#edf7f1}}'
            f'.f{{border:1px solid #29433d;border-radius:12px;padding:12px;margin:10px 0;background:#142522}}.warning,.critical{{border-color:#f3c978}}pre{{white-space:pre-wrap;color:#a8beb4}}</style>'
            f'<h1>{e(APP)}</h1><p>Score <b>{data["score"]}/100 — {e(data["grade"])}</b> · {e(data["device"]["timestamp_utc"])} · {e(data["device"]["platform"])}</p>{rows}')

def save_report(data):
    REPORTS.mkdir(parents=True, exist_ok=True)
    try: os.chmod(BASE, 0o700)
    except OSError: pass
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    body = json.dumps(data, indent=2)
    data["sha256"] = hashlib.sha256(body.encode()).hexdigest()
    body = json.dumps(data, indent=2)
    path = REPORTS / f"guardian-report-{stamp}.json"
    for p, txt in ((path, body), (REPORTS / "latest-report.json", body), (REPORTS / "latest-report.html", render_html(data))):
        p.write_text(txt, encoding="utf-8")
        try: os.chmod(p, 0o600)
        except OSError: pass
    old = sorted(REPORTS.glob("guardian-report-*.json"))
    for p in old[:-MAX_REPORTS]:
        try: p.unlink()
        except OSError: pass
    return path

def history():
    out = []
    for p in sorted(REPORTS.glob("guardian-report-*.json"))[-15:]:
        try:
            d = json.loads(p.read_text()); out.append({"file": p.name, "score": d.get("score"), "grade": d.get("grade"), "when": d["device"]["timestamp_utc"]})
        except Exception: pass
    return out

def safe_cleanup():
    CACHE.mkdir(parents=True, exist_ok=True)
    removed = freed = 0
    for p in CACHE.iterdir():
        try:
            if p.is_file() and p.name.startswith("guardian-temp-"):
                freed += p.stat().st_size; p.unlink(); removed += 1
        except OSError: pass
    return {"files_removed": removed, "bytes_removed": freed, "scope": str(CACHE),
            "note": "Only this app's own explicitly named temporary files are touched. Nothing else on the device is deleted."}

def print_report(d):
    print("\n" + "=" * 62 + f"\n{APP}  v{VERSION}\n" + "=" * 62)
    print(f"Platform: {d['device']['platform']}   Score: {d['score']}/100 ({d['grade']})   Findings: {d['counts']}")
    for x in d["findings"]:
        if x["level"] == "info" and x.get("category") != "ads" and not os.environ.get("GUARDIAN_VERBOSE"): continue
        print(f"\n[{x['level'].upper()}] {x['title']}\n{x['detail']}")
        if x.get("action"): print("Next step:", x["action"])
    print("\n(Set GUARDIAN_VERBOSE=1 to also print INFO items.)")

def selftest():
    ok = True
    def chk(name, cond):
        nonlocal ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name)
    chk("plain https ok", scan_url("https://www.apple.com")["verdict"] == "no_flags")
    chk("ip host flagged", scan_url("http://192.168.0.5/login")["score"] >= 5)
    chk("userinfo disguise", scan_url("https://paypal.com@evil.example/x")["score"] >= 4)
    chk("brand impersonation", scan_url("https://paypal-secure-login.xyz/verify")["verdict"] == "high_risk")
    chk("shortener flagged", scan_url("bit.ly/abc")["score"] >= 3)
    chk("punycode flagged", any("punycode" in r for r in scan_url("https://xn--pple-43d.com")["reasons"]))
    chk("empty handled", scan_url("")["verdict"] == "not_checked")
    chk("garbage handled", scan_url("http://[bad")["verdict"] == "review")
    chk("text scam", scan_url("x") and scan_text("URGENT your account suspended, verify now http://bit.ly/x gift card")["verdict"] == "high_risk")
    chk("text clean", scan_text("See you at lunch at noon")["verdict"] == "no_flags")
    chk("'rate' not stalkerware", not (set(tokens("com.app.rate.me")) & STALKERWARE_EXACT))
    chk("scan runs", run_scan(offline=True)["score"] >= 0)
    real = socket.getaddrinfo
    try:
        def fake(null_ads=True, online=True):
            def g(host, *a, **k):
                if not online: raise socket.gaierror("offline")
                if host in AD_TEST_DOMAINS and null_ads: return [(2, 1, 6, "", ("0.0.0.0", 443))]
                return [(2, 1, 6, "", ("93.184.216.34", 443))]
            return g
        socket.getaddrinfo = fake(True); chk("adblock: strong when ads null-routed", adblock_test()["status"] == "strong")
        socket.getaddrinfo = fake(False); chk("adblock: none when ads resolve", adblock_test()["status"] == "none")
        socket.getaddrinfo = fake(True, online=False); chk("adblock: inconclusive offline", adblock_test()["status"] == "inconclusive")
    finally:
        socket.getaddrinfo = real
    return 0 if ok else 1

def main():
    ap = argparse.ArgumentParser(description=APP)
    ap.add_argument("--scan", action="store_true", help="run diagnostics (default)")
    ap.add_argument("--offline", action="store_true", help="skip network tests")
    ap.add_argument("--json", action="store_true", help="print the full JSON report")
    ap.add_argument("--no-save", action="store_true")
    ap.add_argument("--clean", action="store_true", help="remove only Guardian's own temp files")
    ap.add_argument("--check-url", metavar="URL"); ap.add_argument("--check-text", metavar="TEXT")
    ap.add_argument("--adblock-test", action="store_true", help="test whether ads/trackers are being blocked on this network")
    ap.add_argument("--history", action="store_true"); ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--version", action="store_true")
    a = ap.parse_args()
    if a.version: print(APP, VERSION); return 0
    if a.selftest: return selftest()
    if a.clean: print(json.dumps(safe_cleanup(), indent=2)); return 0
    if a.check_url is not None: print(json.dumps(scan_url(a.check_url), indent=2)); return 0
    if a.check_text is not None: print(json.dumps(scan_text(a.check_text), indent=2)); return 0
    if a.history: print(json.dumps(history(), indent=2)); return 0
    if a.adblock_test:
        r = adblock_test(); print(json.dumps(r, indent=2)); return 0
    d = run_scan(offline=a.offline)
    if not a.no_save: p = save_report(d)
    if a.json: print(json.dumps(d, indent=2))
    else:
        print_report(d)
        if not a.no_save: print(f"\nReport saved: {p}\nOpen {REPORTS/'latest-report.html'} in a browser, or upload latest-report.json to the LifeHaven app.")
    print("\nNo settings were changed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
