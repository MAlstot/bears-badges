"""
BEARS AI Basics: Open Badges 2.0 (hosted verification) generator.

Reads a roster CSV with two columns, email and completed_on (blank means the
student has not finished), and writes Open Badges files for every completer:

  issuer.json, badge.json            the issuer and badge descriptions
  assertions/<CODE>.json             one public record per badge
  images/baked/<CODE>.svg            the student's badge image, record link built in

It also writes a PRIVATE delivery list (email, code, checker link) so each
student can be sent their link. The delivery list must never be published.

Safe to run every night: a student's code comes from a secret key plus their
email, so the same student always gets the same code, records that already
exist are left alone, and only new completers are added.

Usage:
  BADGE_SECRET=<long random text> python3 make_badges.py roster.csv --delivery private/delivery.csv
"""
import argparse, csv, hashlib, hmac, json, os, sys

BASE = "https://malstot.github.io/bears-badges"   # change if the repo name changes
SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CTX = "https://w3id.org/openbadges/v2"
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"      # no 0/O or 1/I mix-ups


def keyed(secret, purpose, email):
    return hmac.new(secret.encode(), f"{purpose}:{email}".encode(), hashlib.sha256).digest()


def code_for(secret, email):
    d = keyed(secret, "code", email)
    chars = "".join(ALPHABET[b % len(ALPHABET)] for b in d[:8])
    return f"BEARS-{chars[:4]}-{chars[4:]}"


def checker_link(code, email):
    return f"{BASE}/?code={code}#email={email}"


def write_json(path, obj):
    full = os.path.join(SITE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        json.dump(obj, f, indent=2)


def write_static():
    write_json("issuer.json", {
        "@context": CTX, "type": "Issuer",
        "id": f"{BASE}/issuer.json",
        "name": "Academy for Teaching and Learning, Baylor University",
        "url": "https://www.baylor.edu/atl/",
        "description": "Issuer of the BEARS AI Basics digital badge (proof of concept)."
    })
    write_json("badge.json", {
        "@context": CTX, "type": "BadgeClass",
        "id": f"{BASE}/badge.json",
        "name": "BEARS AI Basics",
        "description": "Awarded to Baylor undergraduates who complete The BEARS AI Basics, "
                       "an AI literacy microcourse.",
        "image": f"{BASE}/images/bears-badge.svg",
        "criteria": {"narrative": "Complete all required modules of The BEARS AI Basics "
                                  "in Canvas. (Placeholder criteria for the proof of concept.)"},
        "issuer": f"{BASE}/issuer.json",
        "tags": ["AI literacy", "Baylor", "BEARS"]
    })


def issue(roster_path, delivery_path, secret):
    template = open(os.path.join(SITE, "images/bears-badge.svg")).read()
    seen_codes, stats, delivery = {}, {"rows": 0, "not_finished": 0, "new": 0, "existing": 0}, []

    with open(roster_path, newline="") as f:
        for row in csv.DictReader(f):
            stats["rows"] += 1
            email = row["email"].strip().lower()
            done = (row.get("completed_on") or "").strip()
            if not done:
                stats["not_finished"] += 1
                continue

            code = code_for(secret, email)
            if code in seen_codes and seen_codes[code] != email:
                sys.exit(f"Code collision between two students ({code}). Stop and investigate.")
            seen_codes[code] = email

            path = os.path.join(SITE, "assertions", f"{code}.json")
            if os.path.exists(path):
                stats["existing"] += 1
            else:
                salt = keyed(secret, "salt", email).hex()[:16]
                identity = "sha256$" + hashlib.sha256((email + salt).encode()).hexdigest()
                a = {
                    "@context": CTX, "type": "Assertion",
                    "id": f"{BASE}/assertions/{code}.json",
                    "recipient": {"type": "email", "hashed": True, "salt": salt, "identity": identity},
                    "badge": f"{BASE}/badge.json",
                    "verification": {"type": "hosted"},
                    "issuedOn": done if "T" in done else f"{done}T12:00:00Z",
                    "image": f"{BASE}/images/baked/{code}.svg"
                }
                write_json(f"assertions/{code}.json", a)
                baked = template.replace(
                    '<svg xmlns="http://www.w3.org/2000/svg"',
                    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:openbadges="http://openbadges.org"', 1
                ).replace("<!--BAKE-->", f'<openbadges:assertion verify="{a["id"]}"/>', 1)
                os.makedirs(os.path.join(SITE, "images/baked"), exist_ok=True)
                with open(os.path.join(SITE, f"images/baked/{code}.svg"), "w") as out:
                    out.write(baked)
                stats["new"] += 1
            delivery.append({"email": email, "code": code, "completed_on": done,
                             "checker_link": checker_link(code, email),
                             "badge_image": f"{BASE}/images/baked/{code}.svg"})

    if delivery_path:
        os.makedirs(os.path.dirname(os.path.abspath(delivery_path)), exist_ok=True)
        with open(delivery_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(delivery[0]) if delivery else ["email"])
            w.writeheader(); w.writerows(delivery)
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("roster", help="CSV with columns: email, completed_on")
    ap.add_argument("--delivery", help="where to write the PRIVATE delivery list (never publish it)")
    args = ap.parse_args()
    secret = os.environ.get("BADGE_SECRET", "")
    if len(secret) < 32:
        sys.exit("Set BADGE_SECRET to a long random value (32+ characters). Keep it private.")
    write_static()
    s = issue(args.roster, args.delivery, secret)
    print(f"Roster rows: {s['rows']}  Not finished: {s['not_finished']}  "
          f"New badges: {s['new']}  Already issued: {s['existing']}")
