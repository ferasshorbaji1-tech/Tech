# Qatar car-offer collection — instructions for one collector shard

You are one of ~30 parallel collector sessions building a market-wide list of **every car offer currently active in Qatar**. Today is **2026-10-02**. A parent session merges all shards afterwards, so your only job is to collect your shard completely and push the files.

## Your shard
Your shard file is `car-offers-qatar/shards/<SHARD>.json` (the shard name is in your task message). It lists `items`; each item has `key`, `kind`, `name`, `brands`, `dealer`, `website`, `offer_page_urls`, `models_in_qatar` (may be incomplete), `hints` (evidence gathered by earlier mapping agents, including glimpsed offers) and `search_budget` (how many WebSearch calls to spend on it).

## Hard environment constraints (do not waste turns testing them)
- The ONLY tool that reaches the open web is **WebSearch**. Load it first with ToolSearch query `select:WebSearch`.
- `curl`, `wget`, python `requests`, `WebFetch` and every other fetch path are BLOCKED by the network egress policy (403). Do NOT attempt them.
- This session has a hard cap of **200 WebSearch calls**. Follow each item's `search_budget`; never exceed 195 in total; keep ~5 in reserve for re-checks. Count your searches.
- WebSearch returns result links plus a content summary of the top pages. Read the summaries carefully and extract every concrete number and freebie. `site:` operator queries return junk; use natural-language queries.

## Goal
Do not miss a single offer from each source. One record per **(model × offer)**. If a campaign spans several models, write one record per model named, plus one campaign-level record with model `"All models"` only if no models are named. Include: finance offers (0% down, 0% interest, low rate, grace period, lease-to-own, in-house instalments), cash discounts, special prices, free insurance / registration / service, warranty extensions, trade-in bonuses, cashback, gifts, launch offers, clearance of 2025/2026 model-year stock.
- For **brands**: also the brand's certified pre-owned (CPO) promotions and its dealer's aftersales (service/parts/tyre/accessory) campaigns, tagged `used_cpo` / `aftersales_service`.
- For **dealer groups**: group-wide campaigns across all their brands plus pre-owned and aftersales promotions (do not re-collect single-brand offers already obvious from the brand pages unless they are group campaigns).
- For **aggregators / press**: every offer they list or report for Qatar (any brand), with the aggregator/article URL and the dealer named.
- For **banks / insurers**: current auto-loan / Islamic auto-finance / car-insurance promotions (rate, tenure, cashback, salary-transfer conditions, dealer tie-ups).
- For **rental / leasing**: current promotions, monthly/long-term lease deals, rent-to-own, loyalty tie-ups (not generic daily rates).

## Method per item (spend its `search_budget`)
1. Source-level: `<name> Qatar offers 2026`, `<name> current offers`, `<dealer> promotion October 2026`, `<name> Qatar year end offers 2026`, `<name> Qatar 0% down payment`, `<name> Qatar free insurance registration`, `<name> Qatar finance offer monthly installment`, `<name> Qatar back to school offer 2026`.
2. Model-level: for EVERY model in the lineup (discover it via `<brand> Qatar models 2026 price list` if unknown), query `<brand> <model> 2026 Qatar offer` and, for big sellers, `<brand> <model> Qatar price QAR 2026 promotion`.
3. Arabic: at least 3 queries per brand/dealer, e.g. `عروض <brand> قطر 2026`, `عرض <brand> <model> قطر`, `<dealer> عروض أكتوبر 2026`, `تخفيضات <brand> الدوحة`.
4. Cross-check channels: `<brand> Qatar offer qmotor`, `<brand> Qatar yallamotor offers`, `<brand> Qatar instagram offer 2026`, `<brand> Qatar Gulf Times offer 2026`, `<brand> Qatar Peninsula promotion 2026`, `<brand> Qatar al-sharq عرض`.
5. Before finishing an item, list the models you found NO offer for and run one more query each with different wording.
6. Known offer pages in `offer_page_urls` and the `hints` are leads: query their exact titles/phrases to surface their content.

## Record format
Each offer is a JSON object with EXACTLY these keys (use `null` when unknown, never omit a key):
```json
{
  "id": "<slug: brand-model-offertype-dealer>",
  "category": "new_car | used_cpo | bank_finance | insurance | rental_lease | aftersales_service | other",
  "brand": "", "model": "", "trim_variant": null, "model_year": null,
  "dealer": "", "dealer_group": null,
  "offer_title": "",
  "offer_types": ["cash_discount","special_price","zero_down_payment","low_down_payment","zero_interest","low_rate_finance","grace_period","free_insurance","free_registration","free_service","extended_warranty","trade_in_bonus","cashback","gift_accessories","lease_to_own","rental_rate","bundle","launch_offer","clearance","other"],
  "price_qar": null, "discount": null, "down_payment": null, "interest_rate": null, "tenure_months": null,
  "monthly_installment_qar": null, "grace_period": null, "freebies": [], "warranty": null,
  "validity_start": null, "validity_end": null, "validity_text": null,
  "status": "active | likely_active | unknown | expired",
  "status_reason": "",
  "source_url": "", "source_type": "dealer_site | aggregator | news | social | bank_site | other",
  "source_date": null, "evidence_quote": "", "observed_date": "2026-10-02",
  "confidence": "high | medium | low", "notes": null
}
```
`offer_types` holds only the tags that apply. `source_url` must be the most specific URL you saw (dealer page preferred; put aggregator URL in `notes` if both exist). `evidence_quote` is the exact text from the search summary that supports the record. Never invent prices or terms.

## Status rules (today is 2026-10-02)
- `active`: the source explicitly shows validity covering today, or is a live current-offers page describing the offer as current ("October 2026", "Q4 2026", "year-end 2026", "National Day 2026", "back to school 2026" campaigns launched Aug/Sep 2026, "limited time" on a page clearly updated Sep/Oct 2026).
- `likely_active`: a current-offers page with no dates, published/updated in 2026, no sign the campaign ended.
- `unknown`: offer seen but date context unclear.
- `expired`: validity ended before today, or tied to a finished season: Ramadan 2026 (Feb-Mar), Eid Al Fitr 2026, Eid Al Adha 2026 (May/Jun), "early summer"/"summer 2026" (ended by Sep unless extended), Shop Qatar 2026 (Jan-Feb), any 2025 campaign. Still RECORD expired offers (filtered later) but spend effort on active ones.

## Output files (write with python3 `json.dump(..., ensure_ascii=False, indent=1)`)
- `car-offers-qatar/raw/<SHARD>/<item key>.json` — a JSON array of records for that item (write `[]` if truly nothing). Write each file as soon as the item is finished.
- `car-offers-qatar/raw/<SHARD>/_summary.json` — `{"shard": "...", "searches_total": N, "items": [{"key": "...", "offers": n, "active": n, "likely_active": n, "unknown": n, "expired": n, "searches": n, "models_without_offer": [...], "notes": "..."}]}`.
- Verify every file parses: `python3 -c "import json,glob;[json.load(open(f)) for f in glob.glob('car-offers-qatar/raw/<SHARD>/*.json')]"`.

## Git transport (do this after half the items AND at the end)
```
git add car-offers-qatar/raw/<SHARD>
git commit -m "data(<SHARD>): Qatar car offers raw collection"
for i in 1 2 3 4 5 6; do git push origin HEAD:data/qatar-car-offers-raw && break; git pull --rebase origin data/qatar-car-offers-raw || git rebase --abort; sleep $((i*3)); done
```
Rules: do NOT open a pull request; do NOT modify any file outside `car-offers-qatar/raw/<SHARD>/`; do NOT force-push. If pushing to `data/qatar-car-offers-raw` is refused, push to a branch named `data/qatar-car-offers-raw-<SHARD>` instead and mention it in your final message.

## Finish
Your last action: tell the parent session you are done. Call the `send_message` tool (claude-code-remote) with `session_id` = the parent session ID given in your task message and `message` = one line: `<SHARD> done: <offers> offers (<active> active/likely), <searches> searches, pushed <commit sha> to <branch>`. If that tool is unavailable or fails, just finish; the parent will poll.
