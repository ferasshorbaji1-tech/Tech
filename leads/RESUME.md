# Leads verification — state & how to resume

Goal: for every row of `Master_Leads_-_Best_600.xlsx` find the business's real contact email and,
where the held website is wrong (different business / social-only / dead), the correct website.

## State after session 2
- `results.json` — rows 1–210 (session 1, web-search verified).
- `results_A.json … results_H.json` — rule-based cleanup only for rows 211–600 (session 1 agents;
  no search was possible). Statuses contain `NOT SEARCHED` / `NOT VERIFIED` / `needs re-run`.
- `results_R.json` — session 2 re-verification of 210 rows in 211–600 (overrides the A–H files;
  `build.py` loads files in order so later files win).
- Workbook `Master_Leads_-_Best_600_verified.xlsx` status counts: Confirmed 141, Corrected 162,
  Kept-unverified 73, No email found 46, **Not yet searched 178**.

The 178 "Not yet searched" rows all hold an email whose domain matches their own website (e.g.
`info@brymaxlighting.com` / brymaxlighting.com). They are plausible but unconfirmed; they were
deprioritised because the per-session WebSearch cap (200) only allowed ~200 searches and the rows
with junk emails / wrong websites were fixed first.

Also still open (email obfuscated as `[email protected]` in search snippets, direct fetch blocked):
rows 367, 390, 426 and a few "No email found" rows that may have a contact form only.

## To finish in a new session
1. Unblock research in the cloud environment settings (title-bar environment menu → Edit):
   - env var `CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION=600`, and/or
   - broaden **Network access** so company sites can be fetched directly (then a scraper can read each
     site's contact page — this also resolves the obfuscated-email rows).
2. Start a new session on branch `claude/new-session-y2nxda`, open `leads/RESUME.md`.
3. List the rows still unsearched:
   ```bash
   cd leads && python3 - <<'EOF'
   import json,glob,re
   pat=re.compile(r'NOT SEARCHED|NOT VERIFIED|no live search|budget exhausted|needs re-run',re.I)
   res={}
   for f in ['results.json']+sorted(glob.glob('results_[A-Z].json')):
       for k,v in json.load(open(f)).items(): res.setdefault(k,{}).update(v)
   print(sorted(int(k) for k,v in res.items() if pat.search(v.get('status',''))))
   EOF
   ```
4. Per row: `WebSearch "<Company> Qatar <domain> email contact"`; if the snippet shows
   `[email protected]`, one follow-up `"@<domain>"`. Record with
   `python3 recx.py results_S.json '[{"n":…,"email":…,"website":…,"all":…,"source":…,"status":…}]'`
   (new file `results_S.json`; include `website` only when changing it). Status phrases the builder
   understands: "Confirmed via search on their own site", "Email corrected (…)",
   "Website corrected (<old> was wrong)", "Held address kept, unverified (domain matches site)",
   "No email found; …".
5. Rebuild: `python3 build.py` (source workbook path is set at the top of the file).

## Rules used
- Never keep placeholders/junk as the email (example@…, user@domain.com, wordpress@yourdomain.com,
  `.webp` strings, font-designer / theme-vendor credits, delivery-app addresses, another business's domain).
- If the held email's domain matches the company's own site and search can't confirm it → keep, mark unverified.
- If the held website is a different business and no official site is found → use their Facebook/Instagram page and say so.
- Property listings (compounds/towers) keep the listing agency's email, flagged as such.
- Never invent an email; if nothing is found leave it blank and note phone/social in `Check`.
