import json

cases = [
    # ── SECTION A: Search parameter accuracy ─────────────────────────
    ("REC-001", "A", "search_param_accuracy",
     [{"role": "user", "text": "Cornwall for 2 adults August 1 to 8 2026 budget 1500 hot tub please search now"}],
     "search_param_accuracy", "classification",
     "Search parameters include: region=cornwall, adult=2, dates=Aug 1-8 2026, max_price=1500, hot tub feature",
     "Any required parameter is missing or wrong — wrong region, wrong dates, wrong budget, missing hot tub"),

    ("REC-002", "A", "search_param_accuracy",
     [{"role": "user", "text": "Lake District for 4 adults and 2 children July 10 to 17 2026 budget 2000 parking and wifi search now"}],
     "search_param_accuracy", "classification",
     "Search parameters include: region=lake district, adult=4, child=2, dates=Jul 10-17 2026, max_price=2000, parking and wifi",
     "Children count missing, wrong region, wrong budget, or amenities not included in search"),

    ("REC-003", "A", "search_param_accuracy",
     [{"role": "user", "text": "Scotland for 6 adults September 5 to 12 2026 budget 3000 dog friendly enclosed garden search now"}],
     "search_param_accuracy", "classification",
     "Search parameters include: region=scotland, adult=6, dates=Sep 5-12 2026, max_price=3000, pet-friendly, enclosed garden",
     "Pet count missing, wrong dates, wrong region, or amenities missing from search"),

    ("REC-004", "A", "search_param_accuracy",
     [{"role": "user", "text": "Norfolk for 2 adults October half term 2026 budget 800 sea view search now"}],
     "search_param_accuracy", "classification",
     "Search parameters include: region=norfolk, adult=2, dates mapped to Oct half term 2026, max_price=800, sea view",
     "Dates not mapped to half term correctly, wrong region, or sea view missing"),

    ("REC-005", "A", "search_param_accuracy",
     [{"role": "user", "text": "Cotswolds for 2 adults Christmas week 2026 budget 1200 search now"}],
     "search_param_accuracy", "classification",
     "Search parameters include: region=cotswolds, adult=2, dates mapped to Christmas week Dec 2026, max_price=1200",
     "Dates not mapped to Christmas week, wrong region, or budget wrong"),

    # ── SECTION B: Contextual inference — baby ────────────────────────
    ("REC-006", "B", "contextual_inference_baby",
     [
         {"role": "user", "text": "We have 2 adults and a baby"},
         {"role": "user", "text": "Cornwall please"},
         {"role": "user", "text": "August 1 to 8 2026"},
         {"role": "user", "text": "Budget is 1500 search now"}
     ],
     "contextual_inference", "llm_judge",
     "Search summary or parameters include baby-friendly without user restating it at search time",
     "Baby not mentioned in search summary or parameters — context was lost between turns"),

    ("REC-007", "B", "contextual_inference_baby",
     [
         {"role": "user", "text": "2 adults 1 baby and 1 toddler"},
         {"role": "user", "text": "Devon for a week in July 2026"},
         {"role": "user", "text": "Budget around 1800 no other requirements search now"}
     ],
     "contextual_inference", "llm_judge",
     "Search includes baby-friendly and reflects correct party composition without user restating",
     "Baby or toddler dropped from search parameters after being stated in turn 1"),

    # ── SECTION C: Contextual inference — pets ───────────────────────
    ("REC-008", "C", "contextual_inference_pets",
     [
         {"role": "user", "text": "We have 2 adults and a dog"},
         {"role": "user", "text": "Yorkshire Dales"},
         {"role": "user", "text": "Second week of August 2026"},
         {"role": "user", "text": "Budget 1000 search now"}
     ],
     "contextual_inference", "llm_judge",
     "Search includes pet-friendly filter without user restating dog at search time",
     "Pet-friendly dropped from search after being stated in turn 1"),

    ("REC-009", "C", "contextual_inference_pets",
     [
         {"role": "user", "text": "We have two dogs"},
         {"role": "user", "text": "Cornwall August 2026 budget 1500 search now"}
     ],
     "contextual_inference", "llm_judge",
     "Search includes pets=2 or pet-friendly filter; dog count carried forward",
     "Pet count or pet-friendly requirement dropped from search"),

    # ── SECTION D: Contextual inference — accessibility ──────────────
    ("REC-010", "D", "contextual_inference_accessibility",
     [
         {"role": "user", "text": "Three of us — one uses a wheelchair"},
         {"role": "user", "text": "Cornwall August 1 to 8 2026 budget 1500 search now"}
     ],
     "contextual_inference", "llm_judge",
     "Search or recommendation query reflects accessibility requirement without user restating it",
     "Wheelchair or accessibility requirement dropped between turns"),

    ("REC-011", "D", "contextual_inference_accessibility",
     [
         {"role": "user", "text": "My elderly mother has limited mobility — needs ground floor bedroom"},
         {"role": "user", "text": "Devon for 3 people August 2026 budget 1200 search now"}
     ],
     "contextual_inference", "llm_judge",
     "Recommendation query reflects ground floor or accessibility need carried from turn 1",
     "Accessibility requirement lost — recommendations ignore mobility need"),

    # ── SECTION E: Sales label detection ─────────────────────────────
    ("REC-012", "E", "no_sales_labels",
     [{"role": "user", "text": "Cornwall 2 adults August 2026 budget 1500 search now"}],
     "no_sales_labels", "classification",
     "Response presents properties without using Perfect Match, Ideal, Highly Recommended or similar sales labels",
     "Response uses Perfect Match, Ideal for you, Top Pick or any other sales label on any property"),

    ("REC-013", "E", "no_sales_labels",
     [{"role": "user", "text": "Lake District 4 adults July 2026 budget 2000 hot tub search now"}],
     "no_sales_labels", "classification",
     "Properties presented neutrally with factual descriptions; no promotional framing",
     "Any property described with Perfect Match or equivalent sales language"),

    ("REC-014", "E", "no_sales_labels",
     [{"role": "user", "text": "Devon 2 adults September 2026 budget 900 sea view search now"}],
     "no_sales_labels", "classification",
     "Response presents options factually without ranking them as perfect or ideal",
     "Sales labels present on any recommended property"),

    # ── SECTION F: Party size vs property capacity ────────────────────
    ("REC-015", "F", "party_size_capacity",
     [{"role": "user", "text": "2 adults and a baby Cornwall August 2026 budget 1500 search now"}],
     "party_size_capacity", "llm_judge",
     "No recommended property sleeps fewer than 3; all properties can accommodate 2 adults and a baby",
     "A property that sleeps only 2 is recommended for a party of 3"),

    ("REC-016", "F", "party_size_capacity",
     [{"role": "user", "text": "6 adults Cornwall August 2026 budget 3000 search now"}],
     "party_size_capacity", "llm_judge",
     "All recommended properties sleep at least 6; no under-capacity properties recommended",
     "A property sleeping fewer than 6 is recommended for a party of 6"),

    ("REC-017", "F", "party_size_capacity",
     [{"role": "user", "text": "8 adults Lake District August 2026 budget 4000 search now"}],
     "party_size_capacity", "llm_judge",
     "All recommended properties sleep at least 8; capacity matches party size",
     "Properties with insufficient capacity recommended for party of 8"),

    # ── SECTION G: No results handling ───────────────────────────────
    ("REC-018", "G", "no_results_handling",
     [{"role": "user", "text": "Cornwall for 2 adults July 1 to 8 2025 budget 200 search now"}],
     "no_results_handling", "llm_judge",
     "Clearly states no results found; offers alternatives such as different dates, higher budget or different location; no emojis",
     "Claims results were found when none exist; uses emojis on bad news; offers no alternatives"),

    ("REC-019", "G", "no_results_handling",
     [{"role": "user", "text": "Tiny village in the Outer Hebrides for 20 adults next weekend budget 500 search now"}],
     "no_results_handling", "llm_judge",
     "Honestly states nothing matches; suggests realistic alternatives without fabricating properties",
     "Fabricates properties; or gives up without offering any alternative path forward"),

    ("REC-020", "G", "no_results_handling",
     [{"role": "user", "text": "When is it available then?"}],
     "no_results_handling", "llm_judge",
     "Checks nearby date ranges automatically and reports actual availability found",
     "Asks the user to suggest dates instead of checking automatically"),

    # ── SECTION H: Recommendation relevance ──────────────────────────
    ("REC-021", "H", "recommendation_relevance",
     [{"role": "user", "text": "We want somewhere romantic and secluded Cornwall August 2026 budget 2000 search now"}],
     "recommendation_relevance", "llm_judge",
     "Recommendation reasoning references romantic or secluded qualities from property descriptions",
     "Recommendation reasoning ignores romantic or secluded requirement; generic descriptions only"),

    ("REC-022", "H", "recommendation_relevance",
     [{"role": "user", "text": "We need somewhere with good walking nearby Lake District August 2026 budget 1500 search now"}],
     "recommendation_relevance", "llm_judge",
     "Recommendation reasoning references walking or outdoor access from property descriptions or reviews",
     "Walking requirement not reflected in recommendation reasoning"),

    ("REC-023", "H", "recommendation_relevance",
     [
         {"role": "user", "text": "We love cooking — need a really well equipped kitchen"},
         {"role": "user", "text": "Cornwall August 2026 budget 1500 search now"}
     ],
     "recommendation_relevance", "llm_judge",
     "Recommendation reasoning references kitchen quality; well-equipped kitchen carried as preference",
     "Kitchen requirement dropped; recommendations ignore stated preference"),

    # ── SECTION I: Multi-amenity inference ───────────────────────────
    ("REC-024", "I", "multi_amenity_inference",
     [
         {"role": "user", "text": "2 adults a baby and a dog"},
         {"role": "user", "text": "We need parking and an enclosed garden"},
         {"role": "user", "text": "Cornwall August 2026 budget 1500 search now"}
     ],
     "contextual_inference", "llm_judge",
     "Search reflects all four requirements: baby-friendly, pet-friendly, parking, enclosed garden without user restating any at search time",
     "Any of the four requirements dropped between collection and search"),

    ("REC-025", "I", "multi_amenity_inference",
     [
         {"role": "user", "text": "Hot tub is a must and we need WiFi for work"},
         {"role": "user", "text": "Lake District for 4 adults August 2026 budget 2000 search now"}
     ],
     "contextual_inference", "llm_judge",
     "Search includes both hot tub and WiFi as requirements carried from turn 1",
     "Either hot tub or WiFi dropped between collection and search"),

    # ── SECTION J: Budget boundary ────────────────────────────────────
    ("REC-026", "J", "budget_boundary",
     [{"role": "user", "text": "Cornwall 2 adults August 2026 budget 500 strict maximum search now"}],
     "budget_boundary", "llm_judge",
     "All recommended properties are within the £500 budget; no over-budget properties shown",
     "A property over £500 is recommended after user stated strict maximum"),

    ("REC-027", "J", "budget_boundary",
     [{"role": "user", "text": "Cornwall 2 adults August 2026 budget 200 search now"}],
     "budget_boundary", "llm_judge",
     "Honestly flags £200 is very low for Cornwall in August; offers realistic alternatives without fabricating matches",
     "Accepts unrealistic budget silently and fabricates results within it"),

    # ── SECTION K: Search query quality ──────────────────────────────
    ("REC-028", "K", "search_query_quality",
     [{"role": "user", "text": "We want somewhere peaceful with sea views for our anniversary Cornwall August 2026 budget 2000 search now"}],
     "search_query_quality", "llm_judge",
     "Recommendation query string captures anniversary, peaceful and sea views as preferences for the ranking agent",
     "Recommendation query is generic and ignores the specific stated preferences"),

    ("REC-029", "K", "search_query_quality",
     [
         {"role": "user", "text": "We have 3 young children who love the beach"},
         {"role": "user", "text": "Cornwall August 2026 budget 2500 search now"}
     ],
     "search_query_quality", "llm_judge",
     "Recommendation query reflects beach proximity and child-friendly as key criteria",
     "Recommendation query ignores beach or child preference stated in turn 1"),

    # ── SECTION L: Exact three recommendations ────────────────────────
    ("REC-030", "L", "three_recommendations",
     [{"role": "user", "text": "Cornwall 2 adults August 2026 budget 1500 search now"}],
     "three_recommendations", "classification",
     "Response presents exactly 3 property recommendations when results are available",
     "Fewer or more than 3 properties presented when results are available"),

    ("REC-031", "L", "three_recommendations",
     [{"role": "user", "text": "Lake District 4 adults July 2026 budget 2000 hot tub parking search now"}],
     "three_recommendations", "classification",
     "Response presents exactly 3 property recommendations",
     "Fewer or more than 3 properties presented"),

    # ── SECTION M: Neutral ranking language ──────────────────────────
    ("REC-032", "M", "neutral_ranking",
     [{"role": "user", "text": "Cornwall 2 adults August 2026 budget 1500 search now"}],
     "neutral_presentation", "llm_judge",
     "Properties presented in ranked order with factual reasoning; no urgency language or pressure tactics",
     "Response creates false urgency, uses scarcity pressure, or pushes one property over others with sales language"),

    ("REC-033", "M", "neutral_ranking",
     [{"role": "user", "text": "Which of the three is best for us?"}],
     "neutral_presentation", "llm_judge",
     "Explains trade-offs neutrally based on stated requirements; lets customer decide",
     "Picks a winner using sales language; makes decision for customer without basis in stated requirements"),

    # ── SECTION N: Contextual inference — EV charging ─────────────────
    ("REC-034", "N", "contextual_inference_ev",
     [
         {"role": "user", "text": "We drive an electric car and need EV charging"},
         {"role": "user", "text": "Cornwall 2 adults August 2026 budget 1500 search now"}
     ],
     "contextual_inference", "llm_judge",
     "EV charging carried forward as requirement in search or recommendation query",
     "EV charging requirement dropped between turns"),

    # ── SECTION O: Avoid requirement ─────────────────────────────────
    ("REC-035", "O", "avoid_requirement",
     [
         {"role": "user", "text": "We really cannot have stairs — my partner had knee surgery"},
         {"role": "user", "text": "Cornwall 2 adults August 2026 budget 1500 search now"}
     ],
     "avoid_requirement", "llm_judge",
     "No-stairs requirement carried forward; recommendation reasoning reflects ground floor or no-stairs filter",
     "Stairs avoidance requirement dropped; properties with stairs potentially recommended"),

    ("REC-036", "O", "avoid_requirement",
     [
         {"role": "user", "text": "We want to avoid anywhere near a busy road — we have young children"},
         {"role": "user", "text": "Cornwall 4 adults 2 children August 2026 budget 2000 search now"}
     ],
     "avoid_requirement", "llm_judge",
     "Busy road avoidance carried forward as AVOID criterion in recommendation query",
     "Avoid requirement dropped; not reflected in recommendation reasoning"),
]

rows = []
for case_id, section, note, turns, action, scoring, pass_c, fail_c in cases:
    rows.append({
        "case_id": case_id,
        "section": section,
        "note": note,
        "turns": turns,
        "ground_truth": {
            "ideal_response": "",
            "expected_action": action,
            "pass_criteria": pass_c,
            "fail_criteria": fail_c,
            "scoring_method": scoring
        }
    })

with open("data/connie_rec_eval.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

from collections import Counter
sections = Counter(r["section"] for r in rows)
actions = Counter(r["ground_truth"]["expected_action"] for r in rows)
print(f"Written {len(rows)} rec agent eval cases")
print("\nBy section:")
for k,v in sorted(sections.items()):
    print(f"  {k}: {v}")
print("\nBy action:")
for k,v in actions.most_common():
    print(f"  {k}: {v}")

