import json

cases = []

# ── SECTION: Gricean Manner ───────────────────────────────────────────
manner_cases = [
    {
        "case_id": "EXT-001",
        "section": "manner",
        "note": "Clear language — no vague qualifiers",
        "query": {"user_message": "What do you need from me to start searching?"},
        "ground_truth": {
            "ideal_response": "I need three things: where you'd like to go, when you're travelling, and how many people are in your party. Do you have a location in mind?",
            "expected_action": "state_requirements_clearly",
            "pass_criteria": "Lists exactly what is needed in clear, specific terms. Asks one question.",
            "fail_criteria": "Uses vague language like 'a few details' or 'some information'. Asks multiple questions.",
            "scoring_method": "llm_judge"
        }
    },
    {
        "case_id": "EXT-002",
        "section": "manner",
        "note": "Orderly presentation of results",
        "query": {"user_message": "What did you find for Cornwall in August for 2 adults budget 1500?"},
        "ground_truth": {
            "ideal_response": "I found three options. 1) [Property name] — [key feature], £X per week. 2) [Property name] — [key feature], £X per week. 3) [Property name] — [key feature], £X per week. Which would you like to know more about?",
            "expected_action": "present_results_in_order",
            "pass_criteria": "Presents results in a numbered, logical order. Each entry has consistent structure. Ends with one clear question.",
            "fail_criteria": "Presents results in a jumbled or inconsistent format. Mixes details between properties. Asks multiple questions.",
            "scoring_method": "llm_judge"
        }
    },
    {
        "case_id": "EXT-003",
        "section": "manner",
        "note": "No self-contradiction within response",
        "query": {"user_message": "Is the cottage pet friendly?"},
        "ground_truth": {
            "ideal_response": "I don't have that detail to hand — let me check the property listing for you. One moment.",
            "expected_action": "defer_to_lookup",
            "pass_criteria": "Gives a single consistent answer. Either knows or defers — does not say both. No contradictory statements.",
            "fail_criteria": "Says 'yes it is' and then says 'I'm not sure' in the same response. Contradicts itself.",
            "scoring_method": "llm_judge"
        }
    },
    {
        "case_id": "EXT-004",
        "section": "manner",
        "note": "Avoid ambiguous pronoun reference",
        "query": {"user_message": "Tell me more about the second one."},
        "ground_truth": {
            "ideal_response": "The second property is [Property Name] in [Location]. It has [features]. The price is £X for your dates. Would you like to know anything specific about it?",
            "expected_action": "describe_specific_property",
            "pass_criteria": "Names the property explicitly. Does not use ambiguous pronouns like 'it' without clear referent. Clear and specific.",
            "fail_criteria": "Uses 'it' or 'this one' without naming the property. Response is ambiguous about which property is being described.",
            "scoring_method": "llm_judge"
        }
    },
    {
        "case_id": "EXT-005",
        "section": "manner",
        "note": "Logical ordering — most important info first",
        "query": {"user_message": "Is that one available for our dates?"},
        "ground_truth": {
            "ideal_response": "Yes, [Property Name] is available for [dates]. The price for your stay would be £X. Would you like me to share the booking link?",
            "expected_action": "confirm_availability_first",
            "pass_criteria": "States availability answer first, then price, then next step. Logical order.",
            "fail_criteria": "Buries the availability answer mid-response. Leads with irrelevant information.",
            "scoring_method": "llm_judge"
        }
    },
    {
        "case_id": "EXT-006",
        "section": "manner",
        "note": "No unnecessary hedging",
        "query": {"user_message": "Can you search for cottages in Devon for next week?"},
        "ground_truth": {
            "ideal_response": "Of course. How many guests will be travelling, and do you have a budget in mind?",
            "expected_action": "confirm_and_ask_missing_info",
            "pass_criteria": "Confirms clearly and asks for missing info. No unnecessary hedging or qualifiers.",
            "fail_criteria": "Uses excessive hedging like 'I can try to...' or 'I'll do my best to...' before a straightforward task.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-007",
        "section": "manner",
        "note": "Consistent terminology throughout",
        "query": {"user_message": "We want a cottage with a hot tub."},
        "ground_truth": {
            "ideal_response": "Noted — I'll filter for properties with a hot tub. Where are you thinking of going?",
            "expected_action": "confirm_amenity_consistent_terminology",
            "pass_criteria": "Uses consistent terminology — calls it 'hot tub' throughout. Does not switch to 'jacuzzi' or 'spa bath' mid-response.",
            "fail_criteria": "Uses different terms for the same amenity within the same response causing confusion.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-008",
        "section": "manner",
        "note": "Clear transition when changing topic",
        "query": {"user_message": "Actually forget Cornwall, let's try the Lake District instead."},
        "ground_truth": {
            "ideal_response": "No problem — switching to the Lake District. I'll keep your other details: [dates], [party size], [budget]. Shall I search now?",
            "expected_action": "acknowledge_change_and_confirm_retained_info",
            "pass_criteria": "Clearly acknowledges the location change. Confirms what was retained from before. Smooth transition.",
            "fail_criteria": "Ignores the change. Continues with Cornwall. Does not confirm what was retained.",
            "scoring_method": "llm_judge"
        }
    },
]

# ── SECTION: Gricean Quality — Hallucination & Correctness ───────────
quality_cases = [
    {
        "case_id": "EXT-009",
        "section": "quality",
        "note": "No invented property details",
        "query": {"user_message": "Does Primrose Cottage have a sea view?"},
        "ground_truth": {
            "ideal_response": "I don't have that detail without checking the listing. Let me look that up for you.",
            "expected_action": "defer_to_lookup",
            "pass_criteria": "Defers to search/lookup rather than stating a detail it cannot know. Does not invent an answer.",
            "fail_criteria": "States 'yes it has a sea view' or 'no it doesn't' without evidence from a search or tool call.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-010",
        "section": "quality",
        "note": "No invented pricing",
        "query": {"user_message": "How much does it cost for a week in August?"},
        "ground_truth": {
            "ideal_response": "I'll need to check availability and pricing for your specific dates. One moment.",
            "expected_action": "defer_pricing_to_search",
            "pass_criteria": "Does not state a price without running a search. Defers to live data.",
            "fail_criteria": "States a specific price like '£850 per week' without having run a search.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-011",
        "section": "quality",
        "note": "No false availability confirmation",
        "query": {"user_message": "Is it available for the first week of August?"},
        "ground_truth": {
            "ideal_response": "Let me check availability for that week. Bear with me.",
            "expected_action": "check_availability_before_confirming",
            "pass_criteria": "Does not confirm availability without checking. Explicitly says it will check.",
            "fail_criteria": "Says 'yes that week is available' without having checked.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-012",
        "section": "quality",
        "note": "No invented amenity details",
        "query": {"user_message": "Does it have wifi and parking?"},
        "ground_truth": {
            "ideal_response": "I'll check the property details for wifi and parking — I want to make sure I give you accurate information rather than guess.",
            "expected_action": "defer_amenity_to_lookup",
            "pass_criteria": "Does not confirm amenities without checking. Defers to property listing.",
            "fail_criteria": "Confirms 'yes it has wifi and parking' without evidence from a property lookup.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-013",
        "section": "quality",
        "note": "Correct scope — does not claim to book",
        "query": {"user_message": "Can you book it for me?"},
        "ground_truth": {
            "ideal_response": "I can't complete the booking directly, but I can share the booking link for you to confirm it. Shall I do that?",
            "expected_action": "redirect_to_booking_link",
            "pass_criteria": "Correctly states it cannot book directly. Offers booking link as alternative.",
            "fail_criteria": "Claims it can book or implies the booking is confirmed.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-014",
        "section": "quality",
        "note": "No hallucinated search results",
        "query": {"user_message": "Search for pet friendly cottages in Scotland for 4 adults next month budget 1200"},
        "ground_truth": {
            "ideal_response": "Searching for pet-friendly cottages in Scotland for 4 adults in [next month] within £1,200. Here's what I found: [actual results from search tool].",
            "expected_action": "search_and_present_real_results",
            "pass_criteria": "Presents results from an actual search call. Does not fabricate property names or details.",
            "fail_criteria": "Invents property names or details without a search call. Presents fictional results.",
            "scoring_method": "llm_judge"
        }
    },
    {
        "case_id": "EXT-015",
        "section": "quality",
        "note": "Correctness — does not misquote user requirements",
        "query": {"user_message": "We need somewhere for 6 adults not 4 I said that earlier"},
        "ground_truth": {
            "ideal_response": "Apologies for the confusion — I'll update that to 6 adults. Let me re-run the search with the correct party size.",
            "expected_action": "acknowledge_correction_and_update",
            "pass_criteria": "Acknowledges the correction clearly. Updates the requirement. Does not argue or repeat the wrong number.",
            "fail_criteria": "Continues using 4 adults. Argues with the user. Does not acknowledge the correction.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-016",
        "section": "quality",
        "note": "Does not fabricate policies",
        "query": {"user_message": "What is the cancellation policy?"},
        "ground_truth": {
            "ideal_response": "Cancellation policies vary by property. I'd recommend checking the specific terms on the Sykes website or contacting the team directly for accurate details.",
            "expected_action": "defer_policy_to_sykes",
            "pass_criteria": "Defers to Sykes for policy details. Does not invent a specific cancellation policy.",
            "fail_criteria": "States a specific cancellation policy like '48 hours notice' without evidence.",
            "scoring_method": "classification"
        }
    },
]

# ── SECTION: Gricean Relation — Relevance ────────────────────────────
relation_cases = [
    {
        "case_id": "EXT-017",
        "section": "relation",
        "note": "Response directly addresses the question asked",
        "query": {"user_message": "How many bedrooms does it have?"},
        "ground_truth": {
            "ideal_response": "Let me check the property details for the number of bedrooms.",
            "expected_action": "address_bedroom_question_directly",
            "pass_criteria": "Directly addresses the bedroom question. Does not pivot to unrelated topics.",
            "fail_criteria": "Ignores the question and asks about something else. Gives irrelevant information.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-018",
        "section": "relation",
        "note": "No unsolicited information",
        "query": {"user_message": "Just confirm my budget of 1000 pounds."},
        "ground_truth": {
            "ideal_response": "Got it — budget of £1,000. Where are you thinking of travelling?",
            "expected_action": "confirm_and_move_on",
            "pass_criteria": "Confirms the budget and moves to the next missing field. Does not add unsolicited advice or caveats.",
            "fail_criteria": "Adds unsolicited commentary like 'that might be tight for August' or suggests changing the budget unprompted.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-019",
        "section": "relation",
        "note": "Stays on topic when user changes subject",
        "query": {"user_message": "Actually what activities are there in Cornwall?"},
        "ground_truth": {
            "ideal_response": "Cornwall has a lot to offer — coastal walks, surfing, cycling, and great food. It's a lovely choice. Would you like me to focus the search on a particular part of Cornwall?",
            "expected_action": "answer_and_redirect_to_booking",
            "pass_criteria": "Answers the question briefly and naturally redirects toward the booking journey. Stays relevant.",
            "fail_criteria": "Gives an exhaustive tourism guide unrelated to the booking. Loses track of the conversation goal.",
            "scoring_method": "llm_judge"
        }
    },
    {
        "case_id": "EXT-020",
        "section": "relation",
        "note": "Does not answer a different question than asked",
        "query": {"user_message": "Is there a garden?"},
        "ground_truth": {
            "ideal_response": "I'll check whether this property has a garden for you.",
            "expected_action": "answer_garden_question",
            "pass_criteria": "Addresses the garden question specifically. Does not answer a different amenity question.",
            "fail_criteria": "Answers about parking or wifi instead of garden. Misidentifies what was asked.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-021",
        "section": "relation",
        "note": "Relevant follow-up question",
        "query": {"user_message": "We want somewhere in the countryside."},
        "ground_truth": {
            "ideal_response": "Lovely — countryside it is. Do you have a particular region in mind, or would you like me to suggest some popular rural areas?",
            "expected_action": "ask_relevant_followup",
            "pass_criteria": "Follow-up question is directly relevant to narrowing the countryside preference. Not a generic unrelated question.",
            "fail_criteria": "Asks an unrelated question like 'how many guests?' before acknowledging the countryside preference.",
            "scoring_method": "llm_judge"
        }
    },
    {
        "case_id": "EXT-022",
        "section": "relation",
        "note": "Does not introduce irrelevant properties",
        "query": {"user_message": "I only want to see properties in Norfolk."},
        "ground_truth": {
            "ideal_response": "Understood — I'll keep the search to Norfolk only. What dates are you looking at?",
            "expected_action": "confirm_location_constraint",
            "pass_criteria": "Confirms Norfolk as the only location. Does not suggest other regions.",
            "fail_criteria": "Says 'I can also show you Suffolk' or introduces other locations the user did not ask for.",
            "scoring_method": "classification"
        }
    },
]

# ── SECTION: Gricean Quantity — Conciseness ──────────────────────────
quantity_cases = [
    {
        "case_id": "EXT-023",
        "section": "quantity",
        "note": "Response is not too long for a simple confirmation",
        "query": {"user_message": "Yes that sounds good."},
        "ground_truth": {
            "ideal_response": "Great — searching now.",
            "expected_action": "brief_acknowledgement_and_action",
            "pass_criteria": "Response is brief — 1-2 sentences maximum for a simple confirmation. Moves forward immediately.",
            "fail_criteria": "Writes a long paragraph repeating all previously confirmed details before proceeding.",
            "scoring_method": "llm_judge"
        }
    },
    {
        "case_id": "EXT-024",
        "section": "quantity",
        "note": "Does not over-explain scope boundaries",
        "query": {"user_message": "Can you book restaurants too?"},
        "ground_truth": {
            "ideal_response": "I focus on holiday cottages, so restaurants are outside my scope — but I can help you find a great place to stay nearby. Where are you thinking?",
            "expected_action": "brief_scope_redirect",
            "pass_criteria": "Declines briefly and redirects in 1-2 sentences. Does not over-explain.",
            "fail_criteria": "Writes a lengthy explanation of everything it can and cannot do before getting to the point.",
            "scoring_method": "llm_judge"
        }
    },
    {
        "case_id": "EXT-025",
        "section": "quantity",
        "note": "One question only",
        "query": {"user_message": "I am thinking about a holiday in the UK."},
        "ground_truth": {
            "ideal_response": "Lovely! Do you have a part of the UK in mind, or would you like some suggestions?",
            "expected_action": "ask_single_question",
            "pass_criteria": "Asks exactly one question. Warm but brief opening.",
            "fail_criteria": "Asks multiple questions in one response e.g. 'Where? When? How many?'",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-026",
        "section": "quantity",
        "note": "Summary before search is complete but not padded",
        "query": {"user_message": "Yes search now"},
        "ground_truth": {
            "ideal_response": "Searching for: Cornwall, 2 adults, 1–8 August, £1,500 budget. One moment.",
            "expected_action": "brief_summary_before_search",
            "pass_criteria": "Summary is one sentence covering only the confirmed fields. Not padded with filler.",
            "fail_criteria": "Writes a multi-paragraph summary restating everything said in the conversation.",
            "scoring_method": "llm_judge"
        }
    },
    {
        "case_id": "EXT-027",
        "section": "quantity",
        "note": "Property description covers key facts only",
        "query": {"user_message": "Tell me about the first property."},
        "ground_truth": {
            "ideal_response": "The first property is [Name] in [Location]. It sleeps [n], has [key features], and is priced at £[X] for your dates. Would you like more detail or the booking link?",
            "expected_action": "concise_property_description",
            "pass_criteria": "Covers name, location, capacity, key feature, price in 2-3 sentences. Ends with one question.",
            "fail_criteria": "Writes a lengthy paragraph with excessive detail about every amenity before asking what the user wants.",
            "scoring_method": "llm_judge"
        }
    },
    {
        "case_id": "EXT-028",
        "section": "quantity",
        "note": "Does not repeat information already confirmed",
        "query": {"user_message": "And the budget is 1200"},
        "ground_truth": {
            "ideal_response": "Got it — £1,200. Shall I search now?",
            "expected_action": "confirm_without_repetition",
            "pass_criteria": "Confirms the new information only. Does not repeat previously confirmed fields.",
            "fail_criteria": "Repeats all previously confirmed information: 'So you want Cornwall, 2 adults, August, and now a budget of £1,200...'",
            "scoring_method": "classification"
        }
    },
]

# ── SECTION: Memory Persistence (multi-turn) ─────────────────────────
memory_cases = [
    {
        "case_id": "EXT-029",
        "section": "memory_persistence",
        "note": "Dog requirement persists to search turn",
        "turns": [
            {"role": "user", "text": "Hi we are thinking about Cornwall, we have a dog"},
            {"role": "user", "text": "Two adults, first week of August"},
            {"role": "user", "text": "Budget around 1200, search now"}
        ],
        "ground_truth": {
            "ideal_response": "Searching for pet-friendly cottages in Cornwall for 2 adults, 1–8 August, £1,200 budget.",
            "expected_action": "search_with_pet_filter",
            "pass_criteria": "Search includes pet-friendly filter. Dog requirement from Turn 1 is present at search turn.",
            "fail_criteria": "Pet-friendly filter is absent from search. Dog requirement was dropped.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-030",
        "section": "memory_persistence",
        "note": "Baby requirement persists to search turn",
        "turns": [
            {"role": "user", "text": "We are travelling with a baby"},
            {"role": "user", "text": "Lake District, late July"},
            {"role": "user", "text": "4 adults 1 baby budget 2000 search now"}
        ],
        "ground_truth": {
            "ideal_response": "Searching for baby-friendly cottages in the Lake District for 4 adults and 1 baby, late July, £2,000 budget.",
            "expected_action": "search_with_baby_filter",
            "pass_criteria": "Baby-friendly filter included in search. Baby requirement from Turn 1 persists.",
            "fail_criteria": "Baby-friendly requirement dropped. Search treats party as adults only.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-031",
        "section": "memory_persistence",
        "note": "No stairs requirement persists",
        "turns": [
            {"role": "user", "text": "My partner has limited mobility so we need ground floor accommodation, no stairs"},
            {"role": "user", "text": "Devon would be lovely"},
            {"role": "user", "text": "2 adults September 2026 budget 1500 search now"}
        ],
        "ground_truth": {
            "ideal_response": "Searching for ground floor / step-free cottages in Devon for 2 adults, September 2026, £1,500.",
            "expected_action": "search_with_accessibility_filter",
            "pass_criteria": "Accessibility/no stairs requirement included in search. Persists from Turn 1.",
            "fail_criteria": "Accessibility requirement dropped. Standard search run without mobility filter.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-032",
        "section": "memory_persistence",
        "note": "Hot tub requirement persists across topic change",
        "turns": [
            {"role": "user", "text": "We really want a hot tub, that is non negotiable"},
            {"role": "user", "text": "Actually can we change the location to Scotland instead of Cornwall"},
            {"role": "user", "text": "2 adults August budget 2500 search now"}
        ],
        "ground_truth": {
            "ideal_response": "Searching for cottages with a hot tub in Scotland for 2 adults, August, £2,500.",
            "expected_action": "search_with_hot_tub_filter_after_location_change",
            "pass_criteria": "Hot tub filter retained after location change. Both Scotland and hot tub present at search.",
            "fail_criteria": "Hot tub requirement dropped after location change. Only Scotland retained.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-033",
        "section": "memory_persistence",
        "note": "EV charging requirement persists",
        "turns": [
            {"role": "user", "text": "We drive electric so we will need an EV charger at the property"},
            {"role": "user", "text": "Cotswolds, mid October"},
            {"role": "user", "text": "2 adults budget 1800 search now"}
        ],
        "ground_truth": {
            "ideal_response": "Searching for cottages with EV charging in the Cotswolds for 2 adults, mid October, £1,800.",
            "expected_action": "search_with_ev_filter",
            "pass_criteria": "EV charging filter included in search. Persists from Turn 1.",
            "fail_criteria": "EV requirement dropped. Standard search without EV filter.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-034",
        "section": "memory_persistence",
        "note": "Avoid busy roads requirement persists",
        "turns": [
            {"role": "user", "text": "We need somewhere peaceful, away from busy roads, we have young children"},
            {"role": "user", "text": "Norfolk, second week of August"},
            {"role": "user", "text": "2 adults 2 children budget 1400 search now"}
        ],
        "ground_truth": {
            "ideal_response": "Searching for peaceful, rural cottages away from busy roads in Norfolk for 2 adults and 2 children, second week of August, £1,400.",
            "expected_action": "search_with_peaceful_rural_filter",
            "pass_criteria": "Peaceful/away from roads requirement included. Children included in party. Both persist from Turn 1.",
            "fail_criteria": "Peaceful requirement dropped. Standard search run without rural/quiet filter.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-035",
        "section": "memory_persistence",
        "note": "Sea view requirement persists after budget update",
        "turns": [
            {"role": "user", "text": "Sea view is really important to us"},
            {"role": "user", "text": "Cornwall, July, 2 adults"},
            {"role": "user", "text": "Actually we can stretch the budget to 2000, search now"}
        ],
        "ground_truth": {
            "ideal_response": "Searching for sea view cottages in Cornwall for 2 adults, July, £2,000.",
            "expected_action": "search_with_sea_view_after_budget_update",
            "pass_criteria": "Sea view filter retained after budget update. Both £2,000 and sea view present at search.",
            "fail_criteria": "Sea view dropped after budget update. Only updated budget retained.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-036",
        "section": "memory_persistence",
        "note": "Multiple requirements all persist",
        "turns": [
            {"role": "user", "text": "We have a dog and need a hot tub"},
            {"role": "user", "text": "Yorkshire Dales, Easter 2027"},
            {"role": "user", "text": "4 adults budget 2500 search now"}
        ],
        "ground_truth": {
            "ideal_response": "Searching for pet-friendly cottages with a hot tub in the Yorkshire Dales for 4 adults, Easter 2027, £2,500.",
            "expected_action": "search_with_multiple_filters",
            "pass_criteria": "Both pet-friendly AND hot tub filters present at search. Neither dropped.",
            "fail_criteria": "One or both of pet-friendly and hot tub filters dropped at search turn.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-037",
        "section": "memory_persistence",
        "note": "Wheelchair access requirement persists",
        "turns": [
            {"role": "user", "text": "We need wheelchair accessible accommodation"},
            {"role": "user", "text": "Somewhere in the New Forest"},
            {"role": "user", "text": "3 adults September budget 1600 search now"}
        ],
        "ground_truth": {
            "ideal_response": "Searching for wheelchair accessible cottages in the New Forest for 3 adults, September, £1,600.",
            "expected_action": "search_with_wheelchair_filter",
            "pass_criteria": "Wheelchair accessible filter included at search. Persists from Turn 1.",
            "fail_criteria": "Accessibility requirement dropped. Standard search without wheelchair filter.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-038",
        "section": "memory_persistence",
        "note": "Requirement persists across 4 turns",
        "turns": [
            {"role": "user", "text": "We need somewhere with a swimming pool"},
            {"role": "user", "text": "South of England"},
            {"role": "user", "text": "Actually Cornwall specifically"},
            {"role": "user", "text": "2 adults July budget 3000 search now"}
        ],
        "ground_truth": {
            "ideal_response": "Searching for cottages with a swimming pool in Cornwall for 2 adults, July, £3,000.",
            "expected_action": "search_with_pool_filter_after_multiple_turns",
            "pass_criteria": "Swimming pool filter present at search after 4 turns. Not dropped during location refinement.",
            "fail_criteria": "Pool requirement dropped during location changes. Search runs without pool filter.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-039",
        "section": "memory_persistence",
        "note": "Strict no-pets policy persists",
        "turns": [
            {"role": "user", "text": "Important — one of our party has a severe dog allergy so we need a strictly no pets property"},
            {"role": "user", "text": "Lake District, August"},
            {"role": "user", "text": "6 adults budget 3500 search now"}
        ],
        "ground_truth": {
            "ideal_response": "Searching for strictly no-pets cottages in the Lake District for 6 adults, August, £3,500.",
            "expected_action": "search_with_no_pets_filter",
            "pass_criteria": "No-pets filter applied — not pet-friendly filter. Allergy context retained.",
            "fail_criteria": "No-pets requirement dropped or incorrectly applied as pet-friendly.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-040",
        "section": "memory_persistence",
        "note": "Cot requirement persists",
        "turns": [
            {"role": "user", "text": "We will need a cot provided as we have a 6 month old"},
            {"role": "user", "text": "Somewhere in Wales"},
            {"role": "user", "text": "2 adults 1 infant budget 1200 August search now"}
        ],
        "ground_truth": {
            "ideal_response": "Searching for cottages with a cot available in Wales for 2 adults and 1 infant, August, £1,200.",
            "expected_action": "search_with_cot_filter",
            "pass_criteria": "Cot requirement included in search. Infant included in party size.",
            "fail_criteria": "Cot requirement dropped. Infant not reflected in search.",
            "scoring_method": "classification"
        }
    },
]

# ── SECTION: Budget Boundary ──────────────────────────────────────────
budget_cases = [
    {
        "case_id": "EXT-041",
        "section": "budget_boundary",
        "note": "Strict budget — no over-budget suggestions",
        "query": {"user_message": "My absolute maximum is 800 pounds, I cannot go over that"},
        "ground_truth": {
            "ideal_response": "Understood — I'll filter strictly to properties under £800. No over-budget options will be shown.",
            "expected_action": "confirm_strict_budget",
            "pass_criteria": "Confirms the budget as a hard maximum. Does not suggest properties above £800.",
            "fail_criteria": "Suggests properties 'just slightly over' budget. Does not treat £800 as a hard limit.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-042",
        "section": "budget_boundary",
        "note": "Does not suggest stretching budget unprompted",
        "query": {"user_message": "Budget is 600 search now for Cornwall 2 adults August"},
        "ground_truth": {
            "ideal_response": "Searching for cottages in Cornwall for 2 adults in August within £600.",
            "expected_action": "search_within_budget",
            "pass_criteria": "Searches within £600. Does not suggest the budget is too low or recommend increasing it unprompted.",
            "fail_criteria": "Says 'August in Cornwall may be difficult at £600, would you consider increasing your budget?' before searching.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-043",
        "section": "budget_boundary",
        "note": "No results within budget — handles gracefully without suggesting over-budget",
        "query": {"user_message": "Search for cottages in Cornwall 2 adults August budget 400 strict maximum"},
        "ground_truth": {
            "ideal_response": "I couldn't find any available cottages in Cornwall for those dates within £400. Would you like to try a different location, adjust the dates, or I can let you know if anything becomes available?",
            "expected_action": "no_results_within_budget_graceful",
            "pass_criteria": "Acknowledges no results within budget. Offers alternatives without suggesting over-budget properties.",
            "fail_criteria": "Suggests properties above £400. Recommends increasing budget without being asked.",
            "scoring_method": "llm_judge"
        }
    },
    {
        "case_id": "EXT-044",
        "section": "budget_boundary",
        "note": "Budget stated mid-conversation is respected",
        "turns": [
            {"role": "user", "text": "Cornwall 2 adults July"},
            {"role": "user", "text": "The budget is 1000 and that is firm, search now"}
        ],
        "ground_truth": {
            "ideal_response": "Searching for cottages in Cornwall for 2 adults in July within a firm £1,000 budget.",
            "expected_action": "search_with_firm_budget",
            "pass_criteria": "Treats £1,000 as a hard maximum. Does not return results above that figure.",
            "fail_criteria": "Returns or mentions properties above £1,000. Does not respect the firm budget.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-045",
        "section": "budget_boundary",
        "note": "Does not upsell beyond stated budget",
        "query": {"user_message": "We have a budget of 1500 for the week"},
        "ground_truth": {
            "ideal_response": "Got it — £1,500 for the week. Where are you thinking of going?",
            "expected_action": "confirm_budget_no_upsell",
            "pass_criteria": "Confirms budget neutrally. Does not suggest premium options or upsell.",
            "fail_criteria": "Says 'with £1,500 you could also consider our premium range at £2,000' unprompted.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-046",
        "section": "budget_boundary",
        "note": "Budget update replaces previous figure",
        "turns": [
            {"role": "user", "text": "Budget is 1000"},
            {"role": "user", "text": "Actually I can do 1500, search now for Cornwall 2 adults August"}
        ],
        "ground_truth": {
            "ideal_response": "Searching for cottages in Cornwall for 2 adults in August within £1,500.",
            "expected_action": "use_updated_budget",
            "pass_criteria": "Uses updated £1,500 budget. Does not search with old £1,000 figure.",
            "fail_criteria": "Uses £1,000 from Turn 1. Does not update to the new figure.",
            "scoring_method": "classification"
        }
    },
]

# ── SECTION: No Results Handling ──────────────────────────────────────
no_results_cases = [
    {
        "case_id": "EXT-047",
        "section": "no_results",
        "note": "No results — offer alternatives not hallucination",
        "query": {"user_message": "Search for cottages in the Outer Hebrides for 20 adults next week budget 500"},
        "ground_truth": {
            "ideal_response": "I couldn't find anything matching those criteria — the combination of location, party size, dates and budget is quite specific. Would you like to try adjusting the location, extending the budget, or looking at different dates?",
            "expected_action": "no_results_offer_alternatives",
            "pass_criteria": "Acknowledges no results honestly. Offers at least two alternative approaches. Does not invent properties.",
            "fail_criteria": "Invents property names or details. Claims results were found when none were. Gives up without offering alternatives.",
            "scoring_method": "llm_judge"
        }
    },
    {
        "case_id": "EXT-048",
        "section": "no_results",
        "note": "No results — suggests adjusting one parameter at a time",
        "query": {"user_message": "Nothing came up what can I do"},
        "ground_truth": {
            "ideal_response": "A few options: I could widen the search to nearby areas, check different dates, or look at a slightly higher budget if that works for you. Which would you prefer to try first?",
            "expected_action": "suggest_adjustments_one_at_a_time",
            "pass_criteria": "Offers specific actionable alternatives. Asks which to try. Does not overwhelm with options.",
            "fail_criteria": "Says 'sorry nothing available' and stops. Or dumps all possible adjustments at once without guidance.",
            "scoring_method": "llm_judge"
        }
    },
    {
        "case_id": "EXT-049",
        "section": "no_results",
        "note": "No results — does not use emoji",
        "query": {"user_message": "What did you find for that tiny village I asked about"},
        "ground_truth": {
            "ideal_response": "Unfortunately I couldn't find any available properties in that area for your dates. Would you like me to broaden the search to the surrounding region?",
            "expected_action": "no_results_no_emoji",
            "pass_criteria": "Delivers no-results message without emoji. Tone is calm and helpful.",
            "fail_criteria": "Uses emoji when delivering no results. Tone is inappropriately upbeat.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-050",
        "section": "no_results",
        "note": "Unrealistic budget — honest not dismissive",
        "query": {"user_message": "Search Cornwall 2 adults August budget 100"},
        "ground_truth": {
            "ideal_response": "I wasn't able to find any cottages in Cornwall for August within £100 — unfortunately that's below the typical range for that area and time of year. Would you like me to search with a higher budget, or try a different location or time of year?",
            "expected_action": "handle_unrealistic_budget_honestly",
            "pass_criteria": "Honest about why no results found. Not dismissive. Offers constructive alternatives.",
            "fail_criteria": "Simply says 'no results' without explanation. Or ignores the budget issue entirely.",
            "scoring_method": "llm_judge"
        }
    },
    {
        "case_id": "EXT-051",
        "section": "no_results",
        "note": "Availability check fails — suggests alternative dates",
        "query": {"user_message": "When is it available then if not that week"},
        "ground_truth": {
            "ideal_response": "Let me check availability across other dates for that property.",
            "expected_action": "check_alternative_availability",
            "pass_criteria": "Proactively checks availability across other dates. Does not just say it is unavailable and stop.",
            "fail_criteria": "Says 'I cannot check other dates' or stops at unavailability without offering to check alternatives.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-052",
        "section": "no_results",
        "note": "No results — does not fabricate wait times or future availability",
        "query": {"user_message": "Will anything become available soon?"},
        "ground_truth": {
            "ideal_response": "I can't predict future availability, but I can keep searching with adjusted criteria or suggest similar properties in nearby areas. Would either of those help?",
            "expected_action": "honest_about_future_availability",
            "pass_criteria": "Does not fabricate future availability dates. Honest about limitations. Offers realistic alternatives.",
            "fail_criteria": "Says 'something should become available in the next week' without evidence.",
            "scoring_method": "classification"
        }
    },
]

# ── SECTION: Multi-turn Context ───────────────────────────────────────
multi_turn_cases = [
    {
        "case_id": "EXT-053",
        "section": "multi_turn_context",
        "note": "Party composition retained across 5 turns",
        "turns": [
            {"role": "user", "text": "We are 6 adults"},
            {"role": "user", "text": "Looking at Scotland"},
            {"role": "user", "text": "September works for us"},
            {"role": "user", "text": "Budget around 3000"},
            {"role": "user", "text": "Search now"}
        ],
        "ground_truth": {
            "ideal_response": "Searching for cottages in Scotland for 6 adults in September, £3,000 budget.",
            "expected_action": "retain_party_size_across_5_turns",
            "pass_criteria": "6 adults correctly carried to search turn 5. No detail lost across turns.",
            "fail_criteria": "Party size dropped or changed by Turn 5.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-054",
        "section": "multi_turn_context",
        "note": "Location retained after amenity discussion",
        "turns": [
            {"role": "user", "text": "Cornwall please"},
            {"role": "user", "text": "Does it need to have wifi"},
            {"role": "user", "text": "Yes wifi is important"},
            {"role": "user", "text": "2 adults August budget 1500 search now"}
        ],
        "ground_truth": {
            "ideal_response": "Searching for cottages with WiFi in Cornwall for 2 adults in August, £1,500.",
            "expected_action": "retain_location_after_amenity_discussion",
            "pass_criteria": "Cornwall retained as location after WiFi discussion. Both location and WiFi present at search.",
            "fail_criteria": "Location dropped during amenity discussion. Search runs without Cornwall.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-055",
        "section": "multi_turn_context",
        "note": "Date retained after property drilldown",
        "turns": [
            {"role": "user", "text": "Second week of July"},
            {"role": "user", "text": "Lake District 4 adults budget 2000 search now"},
            {"role": "user", "text": "Tell me more about the second property"},
            {"role": "user", "text": "Is it available for those dates"}
        ],
        "ground_truth": {
            "ideal_response": "Let me check availability for the second week of July for that property.",
            "expected_action": "retain_dates_after_drilldown",
            "pass_criteria": "Date from Turn 1 correctly used when checking availability in Turn 4.",
            "fail_criteria": "Asks for dates again in Turn 4. Does not retain dates across the conversation.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-056",
        "section": "multi_turn_context",
        "note": "Special occasion context retained",
        "turns": [
            {"role": "user", "text": "We are celebrating our silver wedding anniversary"},
            {"role": "user", "text": "Devon or Cornwall"},
            {"role": "user", "text": "2 adults July budget 2500"},
            {"role": "user", "text": "Search now"}
        ],
        "ground_truth": {
            "ideal_response": "Searching for romantic cottages in Devon or Cornwall for 2 adults in July, £2,500 — perfect for a silver wedding anniversary.",
            "expected_action": "retain_occasion_context",
            "pass_criteria": "Anniversary context retained and reflected in search framing. Romantic/special filter applied.",
            "fail_criteria": "Anniversary context dropped. Generic search without occasion context.",
            "scoring_method": "llm_judge"
        }
    },
    {
        "case_id": "EXT-057",
        "section": "multi_turn_context",
        "note": "Negative preference retained",
        "turns": [
            {"role": "user", "text": "We do not want anywhere near a main road"},
            {"role": "user", "text": "Cotswolds 4 adults August budget 2000"},
            {"role": "user", "text": "None of those suit us"},
            {"role": "user", "text": "Can you search again with different properties"}
        ],
        "ground_truth": {
            "ideal_response": "Searching again — keeping the no-main-road requirement. Let me find some alternatives in the Cotswolds.",
            "expected_action": "retain_negative_preference_on_retry",
            "pass_criteria": "No-main-road preference retained on retry search. Not dropped after first search failure.",
            "fail_criteria": "No-main-road requirement dropped on second search. Standard search run.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-058",
        "section": "multi_turn_context",
        "note": "Budget retained after location change",
        "turns": [
            {"role": "user", "text": "Cornwall 2 adults August budget 1200"},
            {"role": "user", "text": "Actually can we try Devon instead"},
            {"role": "user", "text": "Search now"}
        ],
        "ground_truth": {
            "ideal_response": "Searching for cottages in Devon for 2 adults in August, £1,200.",
            "expected_action": "retain_budget_after_location_change",
            "pass_criteria": "£1,200 budget retained after location change to Devon. Not dropped.",
            "fail_criteria": "Budget dropped after location change. Search runs without budget filter.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-059",
        "section": "multi_turn_context",
        "note": "Party size retained after amenity negotiation",
        "turns": [
            {"role": "user", "text": "6 adults Lake District September"},
            {"role": "user", "text": "Does it need to sleep 6 or can some share"},
            {"role": "user", "text": "No we need 6 separate beds"},
            {"role": "user", "text": "Budget 3000 search now"}
        ],
        "ground_truth": {
            "ideal_response": "Searching for cottages sleeping 6 in the Lake District for September, £3,000.",
            "expected_action": "retain_party_after_sleeping_discussion",
            "pass_criteria": "6-person capacity retained after sleeping arrangement discussion. Not reduced.",
            "fail_criteria": "Party size or capacity requirement dropped after discussion.",
            "scoring_method": "classification"
        }
    },
    {
        "case_id": "EXT-060",
        "section": "multi_turn_context",
        "note": "Multiple retained across longest conversation",
        "turns": [
            {"role": "user", "text": "We have a large dog and need a hot tub"},
            {"role": "user", "text": "Yorkshire Dales"},
            {"role": "user", "text": "Easter 2027"},
            {"role": "user", "text": "8 adults"},
            {"role": "user", "text": "Budget 4000"},
            {"role": "user", "text": "Search now"}
        ],
        "ground_truth": {
            "ideal_response": "Searching for pet-friendly cottages with a hot tub in the Yorkshire Dales for 8 adults at Easter 2027, £4,000.",
            "expected_action": "retain_all_across_6_turns",
            "pass_criteria": "All fields retained across 6 turns: pet-friendly, hot tub, location, dates, party size, budget.",
            "fail_criteria": "Any field dropped across the 6 turns.",
            "scoring_method": "classification"
        }
    },
]

# ── Assemble all cases ────────────────────────────────────────────────
cases = (
    manner_cases +
    quality_cases +
    relation_cases +
    quantity_cases +
    memory_cases +
    budget_cases +
    no_results_cases +
    multi_turn_cases
)

output_path = "/Users/calbertgraham/Desktop/connie-evaluator/data/connie_extended_eval.jsonl"
with open(output_path, "w", encoding="utf-8") as f:
    for case in cases:
        f.write(json.dumps(case, ensure_ascii=False) + "\n")

print(f"Written {len(cases)} cases to {output_path}")

from collections import Counter
sections = Counter(c["section"] for c in cases)
scoring  = Counter(c["ground_truth"]["scoring_method"] for c in cases)
print("\nBy section:")
for k, v in sorted(sections.items()):
    print(f"  {k}: {v}")
print("\nBy scoring method:")
for k, v in scoring.most_common():
    print(f"  {k}: {v}")
