"""
BEARS AI Basics: Open Badges 2.0 (hosted verification) generator.

Proof of concept. Reads a roster of completers and writes:
  issuer.json, badge.json, assertions/<CODE>.json, images/baked/<CODE>.svg

In a real pipeline, the roster would come from the Canvas API inside a
GitHub Action, and the roster itself would never be committed to the repo.
Only hashed emails are ever published.
"""
import hashlib, json, os, secrets, string, sys
from datetime import datetime, timezone

BASE = "https://malstot.github.io/bears-badges"   # change if the repo name changes
OUT = os.path.join(os.path.dirname(__file__), "..")
CTX = "https://w3id.org/openbadges/v2"
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O or 1/I confusion

def new_code():
    part = lambda: "".join(secrets.choice(ALPHABET) for _ in range(4))
    return f"BEARS-{part()}-{part()}"

def hashed_identity(email, salt):
    norm = email.strip().lower()
    return "sha256$" + hashlib.sha256((norm + salt).encode()).hexdigest()

def write(path, obj):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        json.dump(obj, f, indent=2)

def build(roster):
    write("issuer.json", {
        "@context": CTX, "type": "Issuer",
        "id": f"{BASE}/issuer.json",
        "name": "Academy for Teaching and Learning, Baylor University",
        "url": "https://www.baylor.edu/atl/",
        "description": "Issuer of the BEARS AI Basics digital badge (proof of concept)."
    })
    write("badge.json", {
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
    template = open(os.path.join(OUT, "images/bears-badge.svg")).read()
    issued = []
    for row in roster:
        code = row.get("code") or new_code()
        salt = secrets.token_hex(8)
        a = {
            "@context": CTX, "type": "Assertion",
            "id": f"{BASE}/assertions/{code}.json",
            "recipient": {"type": "email", "hashed": True, "salt": salt,
                          "identity": hashed_identity(row["email"], salt)},
            "badge": f"{BASE}/badge.json",
            "verification": {"type": "hosted"},
            "issuedOn": row["issuedOn"],
            "image": f"{BASE}/images/baked/{code}.svg"
        }
        if row.get("revoked"):
            a["revoked"] = True
            a["revocationReason"] = row["revoked"]
        write(f"assertions/{code}.json", a)
        # "Bake" the assertion URL into a copy of the badge image (Open Badges SVG baking)
        baked = template.replace(
            '<svg xmlns="http://www.w3.org/2000/svg"',
            '<svg xmlns="http://www.w3.org/2000/svg" xmlns:openbadges="http://openbadges.org"', 1
        ).replace("<!--BAKE-->", f'<openbadges:assertion verify="{a["id"]}"/>', 1)
        os.makedirs(os.path.join(OUT, "images/baked"), exist_ok=True)
        open(os.path.join(OUT, f"images/baked/{code}.svg"), "w").write(baked)
        issued.append((code, row["email"], "revoked" if row.get("revoked") else "active"))
    return issued

if __name__ == "__main__":
    roster = json.load(open(sys.argv[1]))
    for code, email, status in build(roster):
        print(f"{code}  {email}  {status}")
