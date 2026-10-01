# Leads verification — state & how to resume

Goal: for every row of `Master_Leads_-_Best_600.xlsx` find the business's real contact email and,
where the held website is wrong (different business / social-only / dead), the correct website.

## What is done
- Rows **1–210**: verified by web search (one search per company, `@domain` follow-ups where the
  address was obfuscated). Results in `results.json` (keyed by row `#`).
- Rows **211–600**: NOT verified online. This session hit the per-session WebSearch cap (200 calls)
  and the environment's network policy blocks fetching business sites directly (WebFetch/curl → 403).
  Background agents applied rule-based cleanup only (placeholder/junk emails removed, `%20` prefixes
  stripped). Their records are in `results_A.json … results_H.json`; every unsearched status contains
  one of: `NOT SEARCHED`, `NOT VERIFIED`, `no live search`, `budget exhausted`, `needs re-run`.
- `Master_Leads_-_Best_600_verified.xlsx` = original workbook + updated Email/Website/Check columns +
  audit columns (`Email status`, `Previous email`, `Previous website`) + a `Legend` sheet.

## To resume in a new session
1. Unblock research — either (or both), in the cloud environment settings (title-bar environment menu → Edit):
   - env var `CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION=1200` (≈1 search per row + follow-ups), and/or
   - broaden **Network access** so company websites can be fetched directly (then a scraper can read
     each site's contact page — more reliable than search snippets).
2. Start a new session on branch `claude/new-session-y2nxda`, open `leads/RESUME.md`.
3. Re-run only the unsearched rows. Find them with:
   ```bash
   cd leads && python3 - <<'EOF'
   import json,glob,re
   pat=re.compile(r'NOT SEARCHED|NOT VERIFIED|no live search|budget exhausted|needs re-run',re.I)
   todo=[]
   for f in ['results.json']+sorted(glob.glob('results_[A-H].json')):
       for k,v in json.load(open(f)).items():
           if pat.search(v.get('status','')): todo.append(int(k))
   done=set(); 
   for f in ['results.json']+sorted(glob.glob('results_[A-H].json')): done|=set(int(k) for k in json.load(open(f)))
   todo+= [n for n in range(1,601) if n not in done]
   print(sorted(set(todo)))
   EOF
   ```
4. Per row: `WebSearch "<Company> Qatar <domain> email contact"`; if the snippet shows
   `[email protected]`, one follow-up `"@<domain>" email`. Record with
   `python3 recx.py results_<slice>.json '[{"n":…,"email":…,"website":…,"all":…,"source":…,"status":…}]'`
   (include `website` only when changing it). Status phrases the builder understands:
   "Confirmed via search on their own site", "Email corrected (…)", "Website corrected (<old> was wrong)",
   "Held address kept, unverified (domain matches site)", "No email found; …".
5. Rebuild the workbook: `python3 build.py` (reads the source xlsx path at the top of the file —
   update `SRC` if the upload path differs).

## Rules used
- Never keep placeholders/junk as the email (example@…, user@domain.com, wordpress@yourdomain.com,
  `.webp` strings, font-designer / theme-vendor credits, delivery-app addresses, another business's domain).
- If the held email's domain matches the company's own site and search can't confirm it → keep, mark unverified.
- If the held website is a different business and no official site is found → use their Facebook/Instagram page and say so.
- Never invent an email; if nothing is found leave it blank and note phone/social in `Check`.
