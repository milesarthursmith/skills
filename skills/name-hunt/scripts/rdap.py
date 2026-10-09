#!/usr/bin/env python3
"""Check exact .com availability against the Verisign RDAP registry.

Usage:
  python3 rdap.py a.com b.com ...
  python3 rdap.py --file domains.txt [more.com ...]

The file holds one domain per line; blank lines and lines starting with # are skipped.

Output, one line per domain:
  name.com               AVAILABLE
  name.com               TAKEN  reg YYYY-MM-DD  exp YYYY-MM-DD  Registrar  status
  name.com               ? http CODE            (000 = no response; retry once)
"""
import sys, json, subprocess, time


AU_BLOCKED = None  # hours left on an auDA block, once seen


def fetch(d):
    # .au domains go to the auDA registry, which rate-limits (429). Short waits are retried;
    # a long Retry-After (auDA can block for ~24h) stops all further .au lookups at once.
    global AU_BLOCKED
    au = d.endswith(".au")
    if au and AU_BLOCKED: return "", f"429 (auDA blocked ~{AU_BLOCKED}h)"
    url = (f"https://rdap.cctld.au/rdap/domain/{d}" if au
           else f"https://rdap.verisign.com/com/v1/domain/{d}")
    for wait in (0, 10, 30, 60):
        time.sleep(wait)
        r = subprocess.run(["curl", "-sS", "-m", "30", "-D", "-", "-w", "\n%{http_code}", url],
                           capture_output=True, text=True)
        out = r.stdout
        body, code = out.rsplit("\n", 1) if "\n" in out else ("", out or "000")
        head, _, body = body.rpartition("\n\n")
        if code.strip() != "429": break
        ra = [l.split(":", 1)[1].strip() for l in head.splitlines() if l.lower().startswith("retry-after:")]
        if ra and ra[0].isdigit() and int(ra[0]) > 300:
            AU_BLOCKED = round(int(ra[0]) / 3600, 1)
            return "", f"429 (auDA blocked ~{AU_BLOCKED}h)"
    if au: time.sleep(5)
    return body, code


def check(d):
    body, code = fetch(d)
    if code.strip() == "404": return f"{d:<22} AVAILABLE"
    if code.strip() != "200": return f"{d:<22} ? http {code.strip()}"
    j = json.loads(body); reg = ""
    for e in j.get("entities", []):
        if "registrar" in e.get("roles", []):
            for v in e.get("vcardArray", [[], []])[1]:
                if v[0] == "fn": reg = v[3]
    ev = {x["eventAction"]: x["eventDate"][:10] for x in j.get("events", [])}
    st = ",".join(s for s in j.get("status", []) if "prohibited" not in s)
    return f"{d:<22} TAKEN  reg {ev.get('registration','?')}  exp {ev.get('expiration','?')}  {reg[:28]:<28} {st}"


def domains(argv):
    out, args = [], iter(argv)
    for a in args:
        if a == "--file":
            path = next(args, None)
            if path is None: sys.exit("--file needs a path")
            with open(path) as f:
                out += [l.strip() for l in f if l.strip() and not l.lstrip().startswith("#")]
        elif a.startswith("--file="):
            with open(a.split("=", 1)[1]) as f:
                out += [l.strip() for l in f if l.strip() and not l.lstrip().startswith("#")]
        else:
            out.append(a)
    return [d.lower() for d in dict.fromkeys(out)]


if __name__ == "__main__":
    ds = domains(sys.argv[1:])
    if not ds: sys.exit(__doc__)
    for d in ds: print(check(d), flush=True)
