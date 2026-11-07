# BEARS AI Basics badges (proof of concept)

Open Badges 2.0 hosted verification for The BEARS AI Basics, issued by the Academy for Teaching and Learning, Baylor University. **All records are fake students.**

## Put it online

1. On GitHub, create a new public repository named **bears-badges**.
2. Click **Add file, then Upload files**, and drag in everything from this folder (keep the folder structure).
3. Go to **Settings, then Pages**. Under Source, pick **Deploy from a branch**, choose **main** and **/ (root)**, and save.
4. After a minute or two, the checker is live at https://malstot.github.io/bears-badges/

If you use a different repo name, the web addresses inside the JSON files need to change. Rerun the script after editing `BASE` in `tools/make_badges.py`.

## Test codes

| Code | Email to enter | Expected result |
|---|---|---|
| `BEARS-E2SX-UHZW` | avery.sample@example.edu | active |
| `BEARS-9B94-5THF` | jordan.testcase@example.edu | active |
| `BEARS-7PRQ-N2L7` | riley.placeholder@example.edu | active |
| `BEARS-C8EA-ZZNX` | casey.demo@example.edu | revoked |

Also try a real code with the wrong email, and a made-up code like BEARS-AAAA-BBBB.

## Files

- `index.html`: the checker professors use
- `about.html`: one-page overview for IT
- `issuer.json`, `badge.json`, `assertions/`: the Open Badges records
- `images/bears-badge.svg`: placeholder art; `images/baked/`: each student's badge with their record link built in
- `tools/make_badges.py`: makes the records from a roster (the roster itself is never uploaded)
