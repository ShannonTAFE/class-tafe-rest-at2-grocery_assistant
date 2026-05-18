# Version 1.5 Signal Vision Ideas

## Purpose

This document captures the broader planning-signal ideas discussed for Version 1.5 and future versions of the Grocery Assistant MCP project.

The purpose is not to implement every idea immediately.

The purpose is to document the long-term signal vision so that Version 1.5A can be designed with enough flexibility to support better planning intelligence over time.

Version 1.5 planning tools should help the connected LLM agent reason more safely and effectively over grocery data.

The planning layer should not only answer:

```text
What data exists?
```

It should help answer:

```text
What is possible?
What is flexible?
What is probably true despite imperfect records?
What is useful to suggest?
What should the agent avoid overclaiming?
What action would require explicit confirmation?
```

---

# Core Planning Principle

Planning signals are not just facts.

They are decision-support cues for the agent.

A raw fact might be:

```json
{
  "food_item": "Spinach",
  "expiry_date": "2026-05-20"
}
```

A useful planning signal is:

```json
{
  "signal_type": "use_soon",
  "food_item": "Spinach",
  "reason": "Spinach expires soon and is otherwise usable.",
  "agent_guidance": "Prioritise this item in meal suggestions if the user wants to reduce waste."
}
```

The second form helps the agent reason.

---

# High-Level Signal Families

The planning layer should eventually support several signal families:

```text
1. Operational signals
2. Data-quality and leniency signals
3. Nutrition-opportunity signals
4. User-preference and enjoyment signals
5. Cost and affordability signals
6. Convenience and effort signals
7. Goal-alignment signals
8. Meal-construction signals
9. Substitution and flexibility signals
10. Behaviour-pattern signals
11. Waste-reduction signals
12. Agent-safety and confirmation signals
```

Not all of these should be implemented in Version 1.5A.

However, the schema should be flexible enough to support them later.

---

# Recommended Signal Domains

The signal schema should support these domains:

```text
inventory
intake
consumption
waste
nutrition
preference
goal
cost
convenience
meal_construction
substitution
data_quality
system
```

## Near-Term Domains for Version 1.5A

Version 1.5A should probably implement only:

```text
inventory
intake
data_quality
system
```

## Future Domains to Reserve

Future versions can expand into:

```text
nutrition
preference
goal
cost
convenience
meal_construction
substitution
waste
consumption
```

This avoids overbuilding Version 1.5A while keeping the architecture future-proof.

---

# Core Signal Object

A signal should use a consistent object shape.

Recommended structure:

```json
{
  "signal_id": "sig_001",
  "domain": "inventory",
  "signal_type": "use_soon",
  "subject": {
    "stock_id": "inv_004",
    "food_item": "Spinach",
    "category": "vegetable"
  },
  "severity": "medium",
  "polarity": "positive",
  "confidence": "high",
  "reason": "Item is available and expires within the use-soon window.",

  "evidence": {
    "source": "user_inventory.csv",
    "evidence_type": "observed",
    "source_fields": ["stock_status", "expiry_date"],
    "source_values": {
      "stock_status": "in_stock",
      "expiry_date": "2026-05-20"
    }
  },

  "interpretation": {
    "agent_use": "prioritise_for_meal_suggestion",
    "safe_to_use_for": [
      "soft_suggestion",
      "meal_planning",
      "waste_reduction_suggestion"
    ],
    "not_safe_to_use_for": [
      "automatic_inventory_deduction"
    ],
    "assumption_level": "low",
    "recommendation_risk": "low"
  },

  "data_quality": {
    "score": 1.0,
    "quality_level": "complete",
    "missing_fields": [],
    "conflicting_fields": [],
    "inference_required": false
  },

  "user_fit": {
    "preference_fit": "unknown",
    "goal_fit": "supports_waste_reduction",
    "cost_fit": "unknown",
    "convenience_fit": "unknown",
    "enjoyment_fit": "unknown"
  },

  "flexibility": {
    "ingredient_role": "vegetable",
    "is_required": false,
    "substitutions_available": false,
    "substitution_candidates": []
  },

  "agent_guidance": "Good candidate to prioritise in meal suggestions, especially if the user wants to reduce waste.",
  "limitations": []
}
```

---

# Core Signal Fields

## `signal_id`

A stable ID within the response.

This allows recommendations to reference supporting signals.

Example:

```json
{
  "recommendation_id": "rec_001",
  "supporting_signal_ids": ["sig_inventory_001", "sig_inventory_004"]
}
```

---

## `domain`

The area the signal belongs to.

Recommended domains:

```text
inventory
intake
consumption
waste
nutrition
preference
goal
cost
convenience
meal_construction
substitution
data_quality
system
```

---

## `signal_type`

The specific kind of planning signal.

Examples:

```text
available_inventory
use_soon
expired
recently_eaten
protein_opportunity
substitution_available
low_cost_meal_opportunity
write_requires_confirmation
```

---

## `subject`

The thing the signal is about.

Examples:

```json
{
  "stock_id": "inv_004",
  "food_item": "Spinach",
  "category": "vegetable"
}
```

or:

```json
{
  "meal_name": "Spaghetti bolognese",
  "meal_type": "dinner"
}
```

or:

```json
{
  "goal": "increase protein",
  "meal_context": "lunch"
}
```

---

## `severity`

How strongly the signal should matter.

Suggested values:

```text
info
low
medium
high
critical
```

Examples:

```text
expired = critical
very_low_stock = high
low_stock = medium
recently_eaten = low or medium
missing optional ingredient = low
```

---

## `polarity`

How the signal affects a recommendation.

Suggested values:

```text
positive
negative
neutral
caution
```

Examples:

```text
available_inventory = positive
expired = negative
low_stock = caution
missing_data = caution
recently_eaten = caution
possible_staple = positive for restock planning
```

The same signal can have different meaning depending on the task.

For example:

```text
out_of_stock
```

For meal suggestions:

```text
negative — cannot use this item
```

For restock suggestions:

```text
positive — possible shopping candidate
```

---

## `confidence`

How reliable the signal is.

Suggested values:

```text
high
medium
low
```

Example:

```json
{
  "signal_type": "possible_staple",
  "confidence": "low",
  "reason": "Item is out of stock and appears to be pantry-related, but no purchase history is available."
}
```

---

## `reason`

A human-readable explanation the agent can reuse.

Example:

```text
Item is available and expires within the use-soon window.
```

---

## `evidence`

Compact source evidence used to create the signal.

Recommended shape:

```json
{
  "source": "user_inventory.csv",
  "evidence_type": "observed",
  "source_fields": ["stock_status", "expiry_date"],
  "source_values": {
    "stock_status": "very_low",
    "expiry_date": "2026-05-20"
  }
}
```

Recommended `evidence_type` values:

```text
observed
user_stated
derived
inferred
assumed
missing
```

This distinction matters because observed data is stronger than inferred data.

---

## `interpretation`

This tells the agent what it can safely do with the signal.

Recommended shape:

```json
{
  "agent_use": "prioritise_for_meal_suggestion",
  "safe_to_use_for": ["soft_suggestion", "meal_planning"],
  "not_safe_to_use_for": ["automatic_inventory_deduction", "precise_nutrition_claim"],
  "assumption_level": "moderate",
  "recommendation_risk": "medium"
}
```

Recommended `assumption_level` values:

```text
none
low
moderate
high
```

Recommended `recommendation_risk` values:

```text
low
medium
high
```

---

## `data_quality`

This helps the system handle imperfect user input.

Recommended shape:

```json
{
  "score": 0.74,
  "quality_level": "usable_with_caution",
  "missing_fields": ["unit"],
  "conflicting_fields": [],
  "inference_required": true
}
```

Suggested `quality_level` values:

```text
complete
usable
usable_with_caution
partial
poor
unusable
```

This is better than relying only on a single leniency score.

The agent needs to know what the data is safe to support.

---

## `user_fit`

This reserves space for future personalization.

Recommended shape:

```json
{
  "preference_fit": "unknown",
  "goal_fit": "supports_waste_reduction",
  "cost_fit": "likely_budget_friendly",
  "convenience_fit": "quick",
  "enjoyment_fit": "unknown"
}
```

This lets future recommendations consider more than availability.

---

## `flexibility`

This supports substitutions and flexible meal construction.

Recommended shape:

```json
{
  "ingredient_role": "vegetable",
  "is_required": false,
  "substitutions_available": true,
  "substitution_candidates": [
    {
      "food_item": "Frozen vegetables",
      "stock_id": "inv_009",
      "fit": "reasonable"
    }
  ]
}
```

---

## `agent_guidance`

Guidance written specifically for the connected LLM agent.

Example:

```text
Do not tell the user this item is available. Treat it only as a restock candidate.
```

or:

```text
This is a planning suggestion only. Ask before logging intake or deducting inventory.
```

This field is especially valuable because MCP tools are designed to support agents.

---

## `limitations`

A list of things the agent should not overclaim.

Example:

```json
[
  "Expiry date is missing.",
  "Servings remaining is blank.",
  "Recent intake was not checked."
]
```

---

# Planning Response Schema

A planning response should not only return signals.

It should also include summaries, warnings, next actions, and safety metadata.

Recommended response shape:

```json
{
  "tool_name": "review_planning_context",
  "status": "success",
  "result_type": "planning_context",
  "summary": "Planning context prepared for agent use.",

  "inputs": {
    "recent_days": 7,
    "include_inventory": true,
    "include_recent_intake": true,
    "include_consumption": false,
    "include_waste": false,
    "include_nutrition_opportunities": false,
    "include_goal_context": false
  },

  "context_summary": {
    "available_inventory_count": 0,
    "attention_item_count": 0,
    "recent_meal_count": 0,
    "data_quality_issue_count": 0,
    "goal_context_available": false,
    "preference_context_available": false,
    "nutrition_context_available": false
  },

  "signal_summary": {
    "inventory": {},
    "intake": {},
    "nutrition": {},
    "preference": {},
    "goal": {},
    "cost": {},
    "convenience": {},
    "meal_construction": {},
    "substitution": {},
    "data_quality": {},
    "system": {}
  },

  "signals": [],

  "opportunity_map": {
    "nutrition_opportunities": [],
    "goal_opportunities": [],
    "cost_opportunities": [],
    "convenience_opportunities": [],
    "waste_reduction_opportunities": [],
    "substitution_opportunities": []
  },

  "recommendations": [],

  "warnings": [],

  "next_actions": [],

  "safety": {
    "read_only": true,
    "inventory_mutation_performed": false,
    "intake_mutation_performed": false,
    "consumption_mutation_performed": false,
    "waste_mutation_performed": false,
    "shopping_list_mutation_performed": false,
    "requires_user_confirmation_before_write": true
  },

  "metadata": {
    "records_checked": {
      "inventory": 0,
      "intake_history": 0,
      "intake_items": 0,
      "consumption": 0,
      "waste": 0
    },
    "max_detailed_signals_returned": 50,
    "version": "1.5A"
  }
}
```

---

# Opportunity Map

The `opportunity_map` is a higher-level grouping of useful planning openings.

Signals are individual observations.

Opportunities are grouped possibilities.

Example:

```json
{
  "opportunity_map": {
    "nutrition_opportunities": [
      {
        "opportunity_type": "protein_opportunity",
        "confidence": "medium",
        "reason": "Protein-rich inventory items are available and recent protein estimates are missing or low.",
        "agent_guidance": "Suggest protein-supporting meals softly."
      }
    ],
    "cost_opportunities": [
      {
        "opportunity_type": "use_existing_inventory",
        "confidence": "medium",
        "reason": "Several meal structures can be formed from current inventory."
      }
    ],
    "substitution_opportunities": [
      {
        "opportunity_type": "vegetable_substitution",
        "missing_item": "spinach",
        "replacement_item": "frozen vegetables",
        "agent_guidance": "Do not block the meal idea."
      }
    ]
  }
}
```

The opportunity map helps the agent say things like:

```text
You have a good opportunity to make something budget-friendly using what you already have, and there is also a chance to use up spinach before it expires.
```

---

# Signal Family Ideas

## 1. Operational Inventory Signals

These are the foundation for meal suggestions and restock suggestions.

Possible signal types:

```text
available_inventory
possibly_available_inventory
unavailable_inventory
low_stock
very_low_stock
out_of_stock
expired
unknown_stock_status
stock_id_available
stock_id_missing
```

Example:

```json
{
  "signal_type": "available_inventory",
  "domain": "inventory",
  "subject": {
    "stock_id": "inv_002",
    "food_item": "Rice",
    "category": "pantry"
  },
  "severity": "info",
  "polarity": "positive",
  "confidence": "high",
  "reason": "Rice is marked in_stock.",
  "agent_guidance": "Can be considered for meal suggestions."
}
```

---

## 2. Expiry and Use-Soon Signals

Possible signal types:

```text
expired
expires_today
use_soon
long_life
no_expiry_data
invalid_expiry_date
```

Example:

```json
{
  "signal_type": "use_soon",
  "severity": "medium",
  "polarity": "positive",
  "reason": "Spinach expires in 2 days.",
  "agent_guidance": "Prioritise this item in meal suggestions if it is otherwise usable."
}
```

Expired items should be handled differently:

```json
{
  "signal_type": "expired",
  "severity": "critical",
  "polarity": "negative",
  "agent_guidance": "Do not suggest this item as usable. It may be mentioned for disposal or replacement planning only."
}
```

---

## 3. Quantity Sufficiency Signals

Stock status alone may not be enough.

Possible signal types:

```text
quantity_sufficient
quantity_limited
quantity_unknown
unit_ambiguous
servings_sufficient
servings_limited
```

Example:

```json
{
  "signal_type": "quantity_limited",
  "severity": "medium",
  "polarity": "caution",
  "confidence": "medium",
  "reason": "Only 1 serving appears to remain.",
  "evidence": {
    "source_fields": ["servings_remaining"],
    "source_values": {
      "servings_remaining": 1
    }
  },
  "agent_guidance": "Treat as usable for a small meal or side, not as a main ingredient for multiple servings."
}
```

This should be cautious because units may vary.

---

## 4. Data-Quality and Leniency Signals

User records will not always be perfect.

The system should not fail just because input is incomplete.

Possible signal types:

```text
usable_with_leniency
missing_stock_status
missing_quantity
missing_unit
missing_expiry_date
invalid_expiry_date
missing_category
ambiguous_category
blank_food_item
duplicate_possible
conflicting_stock_status_and_quantity
expired_but_in_stock
out_of_stock_but_positive_quantity
```

Example:

```json
{
  "signal_type": "usable_with_leniency",
  "domain": "data_quality",
  "subject": {
    "stock_id": "inv_012",
    "food_item": "Chicken"
  },
  "severity": "low",
  "polarity": "caution",
  "confidence": "medium",
  "reason": "The item has a food name and category, but quantity and unit are missing.",
  "data_quality": {
    "score": 0.62,
    "quality_level": "partial",
    "missing_fields": ["quantity", "unit"],
    "reliable_fields": ["food_item", "category", "stock_status"]
  },
  "interpretation": {
    "assumption_level": "moderate",
    "fallback_available": true,
    "fallback_strategy": "Suggest as possible ingredient but avoid claiming enough quantity."
  },
  "agent_guidance": "You may mention this item as possibly available, but ask the user to confirm quantity before making it central to a meal."
}
```

## Leniency Concept

A single `leniency_score` is not enough.

Better:

```json
{
  "data_interpretation": {
    "data_quality_score": 0.62,
    "quality_level": "partial",
    "assumption_level": "moderate",
    "recommendation_risk": "medium",
    "safe_to_use_for": ["soft_suggestion", "shopping_prompt"],
    "not_safe_to_use_for": ["automatic_inventory_deduction", "precise_nutrition_claim"]
  }
}
```

The key question is not only:

```text
How good is the data?
```

It is:

```text
What can the agent safely do with this data?
```

---

## 5. Nutrition-Opportunity Signals

Nutrition signals should be framed as soft opportunities, not strict medical advice.

Possible signal types:

```text
protein_opportunity
fibre_opportunity
vegetable_opportunity
wholegrain_opportunity
balanced_meal_opportunity
high_sodium_caution
low_nutrition_confidence
nutrition_data_missing
nutrition_claims_limited
nutrition_estimate_low_confidence
```

Example:

```json
{
  "signal_id": "sig_nutrition_001",
  "domain": "nutrition",
  "signal_type": "protein_opportunity",
  "subject": {
    "meal_context": "dinner",
    "candidate_items": ["eggs", "chicken breast", "Greek yoghurt"]
  },
  "severity": "info",
  "polarity": "positive",
  "confidence": "medium",
  "reason": "Recent intake records show several meals with missing or low protein estimates, and protein-rich inventory items are available.",
  "evidence": {
    "source_fields": ["protein_g_estimate", "nutrition_confidence", "category"],
    "source_values": {
      "recent_protein_estimates": "missing_or_low_confidence",
      "available_categories": ["protein", "dairy"]
    }
  },
  "agent_guidance": "Suggest protein-supporting options softly. Do not make medical or strict dietary claims.",
  "limitations": [
    "Nutrition estimates may be incomplete.",
    "No formal nutrition goal has been confirmed by the user."
  ]
}
```

Important boundaries:

```text
Do not make medical claims.
Do not prescribe diets.
Do not overclaim if nutrition estimates are missing.
Do not silently overwrite user-entered nutrition totals.
```

---

## 6. Goal-Alignment Signals

The system may eventually help users work toward long-term food goals slowly.

Possible goals:

```text
eat more protein
reduce food waste
save money
cook more at home
eat more vegetables
prepare for gym or performance goals
reduce takeaway
make faster lunches
use pantry items first
meal prep more consistently
```

Possible signal types:

```text
goal_alignment
goal_conflict
goal_unknown
small_step_goal_opportunity
performance_goal_support
budget_goal_support
waste_reduction_goal_support
meal_prep_goal_support
```

Example:

```json
{
  "signal_id": "sig_goal_001",
  "domain": "goal",
  "signal_type": "small_step_goal_opportunity",
  "subject": {
    "goal": "increase protein",
    "meal_context": "lunch"
  },
  "severity": "info",
  "polarity": "positive",
  "confidence": "medium",
  "reason": "The user has available eggs and tuna, which could support a higher-protein lunch option.",
  "agent_guidance": "Frame this as a small optional step, not as a strict diet instruction.",
  "limitations": [
    "Goal may be temporary or unconfirmed.",
    "No target macro values are confirmed."
  ]
}
```

Goal source types should be distinguished:

```text
user_stated_goal
agent_inferred_goal
temporary_request_goal
system_default_goal
```

The agent should treat user-stated goals as stronger than inferred goals.

---

## 7. Performance and Long-Term Food Goal Signals

Future versions could support performance-oriented planning.

Possible signal types:

```text
training_day_support
recovery_meal_opportunity
higher_protein_meal_opportunity
carbohydrate_energy_opportunity
meal_timing_support
meal_prep_consistency_support
goal_progress_context_missing
```

Examples of future user requests:

```text
Help me eat better for gym training.
Suggest higher-protein dinners this week.
Help me reduce takeaway slowly.
Help me meal prep lunches for work.
```

Important boundaries:

```text
Frame suggestions as general food planning.
Avoid medical or clinical nutrition claims.
Ask for confirmation before storing long-term goals.
Support slow, realistic behaviour changes.
```

---

## 8. Preference and Enjoyment Signals

A meal can be available and nutritious but still be a poor recommendation if the user dislikes it.

Possible signal types:

```text
liked_food
disliked_food
frequently_eaten
rarely_eaten
comfort_food
preferred_cuisine
preferred_meal_format
repetition_tolerance
avoid_repetition
enjoyment_unknown
```

Sources may include:

```text
explicit user preferences
frequent logged intake
repeated restocks
notes fields
meal completion patterns
leftovers patterns
waste patterns
```

Example:

```json
{
  "signal_id": "sig_preference_001",
  "domain": "preference",
  "signal_type": "frequently_eaten",
  "subject": {
    "meal_name": "Spaghetti bolognese",
    "meal_family": "pasta"
  },
  "severity": "info",
  "polarity": "positive",
  "confidence": "medium",
  "reason": "Similar pasta meals appear multiple times in recent intake history.",
  "agent_guidance": "This may indicate preference, but avoid recommending it too often unless repetition is acceptable.",
  "limitations": [
    "Frequency does not always mean preference.",
    "Could reflect convenience rather than enjoyment."
  ]
}
```

Important distinction:

```text
Frequent behaviour does not always equal enjoyment.
```

The user may repeat meals because they are cheap, easy, or available.

---

## 9. Cost and Affordability Signals

Cost matters for grocery planning.

Possible signal types:

```text
low_cost_meal_opportunity
high_cost_ingredient_caution
use_existing_inventory_saves_cost
bulk_item_available
budget_friendly_substitution
shopping_cost_unknown
```

Example:

```json
{
  "signal_id": "sig_cost_001",
  "domain": "cost",
  "signal_type": "use_existing_inventory_saves_cost",
  "subject": {
    "candidate_meal": "Rice and egg bowl"
  },
  "severity": "info",
  "polarity": "positive",
  "confidence": "medium",
  "reason": "The core ingredients appear to already be available in inventory.",
  "agent_guidance": "Mention this as likely budget-friendly because it uses existing items, not because exact prices are known.",
  "limitations": [
    "No price data is recorded.",
    "Cost estimate is approximate."
  ]
}
```

Cost signals should avoid pretending exact price knowledge exists unless price data is actually stored.

---

## 10. Convenience and Effort Signals

Real recommendations should consider effort.

Possible signal types:

```text
quick_meal_opportunity
low_prep_meal
batch_cook_candidate
leftover_friendly
requires_cooking
requires_defrosting
missing_time_context
```

Example:

```json
{
  "signal_id": "sig_effort_001",
  "domain": "convenience",
  "signal_type": "quick_meal_opportunity",
  "subject": {
    "candidate_meal": "Egg fried rice"
  },
  "severity": "info",
  "polarity": "positive",
  "confidence": "medium",
  "reason": "Uses simple pantry and protein items that are commonly quick to prepare.",
  "agent_guidance": "Offer this when the user wants a fast meal. Do not assume exact cooking time."
}
```

This allows the agent to respond differently to:

```text
What should I cook tonight?
```

versus:

```text
What can I eat quickly before work?
```

---

## 11. Meal-Construction Signals

The system does not need a full recipe engine at first.

It can reason with flexible meal structures.

Possible meal archetypes:

```text
rice bowl
pasta meal
stir fry
sandwich
wrap
omelette
salad bowl
soup
snack plate
leftover meal
batch cook
```

Possible ingredient roles:

```text
base
protein
vegetable
flavour
sauce
fat
crunch
side
snack_component
```

Possible signal types:

```text
meal_base_available
protein_available
vegetable_available
flavour_component_available
sauce_or_fat_available
complete_meal_possible
partial_meal_possible
snack_possible
side_dish_possible
ingredient_role_covered
ingredient_role_missing
```

Example:

```json
{
  "signal_id": "sig_meal_structure_001",
  "domain": "meal_construction",
  "signal_type": "complete_meal_possible",
  "subject": {
    "meal_archetype": "rice_bowl",
    "candidate_items": {
      "base": "rice",
      "protein": "chicken",
      "vegetable": "spinach"
    }
  },
  "severity": "info",
  "polarity": "positive",
  "confidence": "medium",
  "reason": "Inventory appears to contain a base, protein, and vegetable suitable for a simple bowl meal.",
  "agent_guidance": "Suggest as a flexible meal idea rather than a fixed recipe."
}
```

This supports intelligent meal planning without needing exact recipes yet.

---

## 12. Substitution and Flexibility Signals

A missing ingredient should not automatically block a meal suggestion.

Possible signal types:

```text
missing_optional_ingredient
missing_required_ingredient
substitution_available
substitution_needed
flexible_recipe_candidate
ingredient_role_covered
ingredient_role_missing
```

Example:

```json
{
  "signal_id": "sig_substitution_001",
  "domain": "substitution",
  "signal_type": "substitution_available",
  "subject": {
    "missing_item": "spinach",
    "replacement_item": "frozen vegetables",
    "ingredient_role": "vegetable"
  },
  "severity": "info",
  "polarity": "positive",
  "confidence": "medium",
  "reason": "A vegetable component is missing, but another vegetable option appears available.",
  "agent_guidance": "Do not reject the meal. Suggest the replacement naturally."
}
```

Core idea:

```text
Judge whether the ingredient role is covered, not only whether the exact item exists.
```

Example:

```text
Spinach missing, but frozen vegetables available = meal may still work.
Chicken missing, but tuna available = possible protein substitution depending on meal type.
Sauce missing = may still work if herbs or basic condiments exist.
```

---

## 13. Behaviour-Pattern Signals

These signals help the agent detect patterns from historical records.

Possible signal types:

```text
recently_eaten
repeated_meal
repeated_category
meal_type_gap
meal_variety_opportunity
frequent_takeaway
home_cooking_opportunity
meal_logging_sparse
```

Example:

```json
{
  "signal_type": "repeated_meal",
  "domain": "intake",
  "subject": {
    "meal_name": "Spaghetti bolognese",
    "meal_type": "dinner"
  },
  "severity": "medium",
  "polarity": "caution",
  "confidence": "high",
  "reason": "Spaghetti bolognese appears multiple times in recent dinner records.",
  "agent_guidance": "Avoid suggesting another pasta-based dinner unless inventory strongly supports it or the user asks."
}
```

This helps avoid repetitive suggestions.

---

## 14. Waste-Reduction Signals

Waste planning can support better shopping and meal suggestions.

Possible signal types:

```text
waste_risk
repeated_waste_item
repeated_waste_category
expired_before_use
buy_smaller_quantity_candidate
use_soon_to_reduce_waste
```

Example:

```json
{
  "signal_type": "repeated_waste_category",
  "domain": "waste",
  "subject": {
    "category": "vegetable"
  },
  "severity": "medium",
  "polarity": "caution",
  "confidence": "medium",
  "reason": "Vegetables appear repeatedly in waste records.",
  "agent_guidance": "When drafting shopping suggestions, consider smaller quantities or longer-lasting alternatives."
}
```

This belongs later than Version 1.5A, but the schema should allow it.

---

## 15. Consumption Velocity Signals

Consumption history can improve restock suggestions.

Possible signal types:

```text
recently_consumed_inventory
fast_consumption
slow_consumption
no_recent_consumption
restock_frequency_candidate
```

Example:

```json
{
  "signal_type": "fast_consumption",
  "domain": "consumption",
  "subject": {
    "stock_id": "inv_010",
    "food_item": "Eggs"
  },
  "severity": "medium",
  "polarity": "positive",
  "confidence": "medium",
  "reason": "Eggs have recent consumption events and are now very low.",
  "agent_guidance": "Prioritise for restock suggestions."
}
```

---

## 16. Linked-Record Integrity Signals

These signals help the agent decide whether inventory-linked workflows are safe.

Possible signal types:

```text
stock_id_available
stock_id_missing
stock_id_invalid
intake_parent_link_valid
intake_child_link_valid
consumption_link_available
consumption_link_missing
```

Example:

```json
{
  "signal_type": "stock_id_available",
  "domain": "inventory",
  "subject": {
    "food_item": "Chicken breast",
    "stock_id": "inv_002"
  },
  "severity": "info",
  "polarity": "positive",
  "confidence": "high",
  "reason": "Inventory item has a valid stock_id.",
  "agent_guidance": "Can be used in inventory-linked meal logging if the user confirms."
}
```

This supports future agent behaviour where inventory-linked workflows are only used when stock IDs are known or confirmed.

---

## 17. Conflict and Contradiction Signals

CSV data may become inconsistent.

Possible signal types:

```text
conflicting_stock_status_and_quantity
expired_but_in_stock
out_of_stock_but_positive_quantity
missing_parent_record
duplicate_inventory_candidate
```

Example:

```json
{
  "signal_type": "conflicting_stock_status_and_quantity",
  "domain": "inventory",
  "severity": "high",
  "polarity": "caution",
  "confidence": "high",
  "reason": "Item is marked out of stock but has quantity greater than zero.",
  "agent_guidance": "Do not rely on this item for meal suggestions without user confirmation."
}
```

This is important for imperfect user data.

---

## 18. User-Confirmation and Safety Signals

Some safety concepts belong both in the global safety block and as individual signals.

Possible signal types:

```text
write_requires_confirmation
inventory_deduction_requires_confirmation
shopping_list_creation_requires_confirmation
nutrition_recalculation_requires_confirmation
recommendations_are_not_actions
```

Example:

```json
{
  "signal_type": "inventory_deduction_requires_confirmation",
  "domain": "system",
  "severity": "high",
  "polarity": "caution",
  "confidence": "high",
  "reason": "Logging this suggested meal with inventory items would deduct tracked inventory.",
  "agent_guidance": "Ask the user before using add_meal_with_inventory_items."
}
```

---

# Recommendation Schema

Recommendations should reference supporting signals instead of repeating everything.

Recommended shape:

```json
{
  "recommendation_id": "rec_001",
  "recommendation_type": "meal_suggestion",
  "title": "Chicken rice bowl",
  "priority": "high",
  "confidence": "medium",
  "summary": "A practical dinner option using available chicken and rice.",
  "supporting_signal_ids": [
    "sig_inventory_001",
    "sig_inventory_002"
  ],
  "caution_signal_ids": [
    "sig_inventory_006"
  ],
  "reason": "Core ingredients are available, but vegetables were not found.",
  "agent_guidance": "Present this as a good option, but mention optional missing vegetables.",
  "safe_follow_up_tools": [
    {
      "tool_name": "add_meal_with_inventory_items",
      "requires_confirmation": true,
      "when_to_use": "Use only if the user wants to log the meal and deduct linked inventory."
    },
    {
      "tool_name": "add_meal_with_items",
      "requires_confirmation": true,
      "when_to_use": "Use if the user wants to log intake without inventory deduction."
    }
  ]
}
```

---

# Warning Schema

Warnings are response-level guidance.

Signals are observations.

Warnings tell the agent how to avoid overclaiming.

Recommended shape:

```json
{
  "warning_type": "limited_data",
  "severity": "medium",
  "message": "Recent intake records were not found.",
  "agent_guidance": "Do not claim that suggestions avoid recently eaten meals."
}
```

Useful warning types:

```text
limited_inventory_data
limited_intake_data
limited_consumption_data
limited_waste_data
invalid_dates_found
ambiguous_units_found
write_requires_confirmation
recommendations_are_not_actions
nutrition_context_missing
goal_context_missing
preference_context_missing
cost_context_missing
```

---

# Next Action Schema

Next actions help the agent route follow-up intent safely.

Recommended shape:

```json
{
  "action_type": "ask_user_to_confirm",
  "label": "Confirm before writing records",
  "tool_name": null,
  "requires_confirmation": true,
  "reason": "Planning tools are read-only."
}
```

Other examples:

```json
{
  "action_type": "log_with_inventory_items",
  "label": "Log this meal with inventory deduction",
  "tool_name": "add_meal_with_inventory_items",
  "requires_confirmation": true,
  "reason": "This would create intake rows and deduct inventory."
}
```

Recommended action types:

```text
read_more
ask_user_to_confirm
log_intake_only
log_with_inventory_items
draft_shopping_list
update_inventory
review_low_stock
suggest_restock
```

---

# Safety Block

Every planning response should include a safety block.

Recommended shape:

```json
{
  "read_only": true,
  "inventory_mutation_performed": false,
  "intake_mutation_performed": false,
  "consumption_mutation_performed": false,
  "waste_mutation_performed": false,
  "shopping_list_mutation_performed": false,
  "requires_user_confirmation_before_write": true
}
```

This helps the agent understand:

```text
This was only a suggestion.
No records were changed.
A write needs confirmation.
```

---

# Signal Filtering and Noise Control

More signals are not always better.

Bad signal design can produce:

```text
20 signals per item
500 total signals
large JSON response
agent confusion
lower recommendation quality
```

Recommended strategy:

```text
Return all high and critical signals.
Return medium caution signals.
Return top N positive planning signals.
Return summary counts for low-level signals.
Avoid dumping every possible signal.
```

Example summary:

```json
{
  "signal_summary": {
    "inventory": {
      "available_count": 18,
      "low_stock_count": 3,
      "expired_count": 1,
      "use_soon_count": 2,
      "data_quality_issue_count": 4
    }
  }
}
```

---

# Version 1.5A Suggested Foundation Signals

Version 1.5A should implement a small but useful foundation set.

Suggested initial signal types:

```text
available_inventory
low_stock
very_low_stock
out_of_stock
expired
use_soon
no_expiry_data
missing_stock_status
missing_quantity
missing_unit
recently_eaten
no_recent_intake_records
stock_id_available
write_requires_confirmation
recommendations_are_not_actions
```

This supports:

```text
review_planning_context
future low-stock review
future restock suggestions
future meal suggestions
future next-meal suggestions
```

---

# Signals to Defer Until Later

These are valuable but should probably not be implemented in 1.5A.

```text
possible_staple
fast_consumption
waste_risk
repeated_waste_category
complete_meal_possible
partial_meal_possible
missing_required_ingredient
substitution_available
nutrition_claims_limited
protein_opportunity
goal_alignment
cost_opportunity
convenience_opportunity
duplicate_inventory_candidate
conflicting_stock_status_and_quantity
```

The schema should support them, but the first implementation does not need all of them.

---

# Practical Scoring Ideas

## Data Quality Score

A rough score from `0.0` to `1.0`.

Example interpretation:

```text
0.90 - 1.00 = complete
0.75 - 0.89 = usable
0.50 - 0.74 = usable_with_caution
0.25 - 0.49 = poor
0.00 - 0.24 = unusable
```

## Assumption Level

```text
none
low
moderate
high
```

## Recommendation Risk

```text
low
medium
high
```

## Confidence

```text
high
medium
low
```

These should remain simple at first.

Avoid over-engineering numeric confidence before the system has enough data.

---

# Important Design Boundaries

## Suggestions Are Not Actions

Planning tools may suggest, rank, explain, and draft.

They should not silently mutate:

```text
inventory records
intake records
inventory consumption records
waste records
shopping list records
```

Any mutation should continue to route through explicit, tested write tools.

---

## Soft Nutrition Only

Nutrition-related signals should be framed as opportunities.

Avoid:

```text
medical claims
strict diet prescriptions
clinical nutrition advice
overconfident macro claims from weak data
silent recalculation of user-entered nutrition totals
```

Prefer:

```text
This could support a higher-protein meal.
This may be a good fibre opportunity.
Based on available estimates, this seems more balanced.
Nutrition data is incomplete, so treat this as approximate.
```

---

## Imperfect Data Should Not Break Planning

The system should be lenient with imperfect records.

But leniency should be explicit.

The agent should know when data is:

```text
complete
usable
usable with caution
partial
poor
unusable
```

The agent should also know what the data is safe to support.

---

## Frequency Does Not Always Mean Preference

Repeated eating may suggest preference, but it may also indicate:

```text
convenience
cost constraints
limited inventory
meal prep leftovers
lack of alternatives
```

Preference signals should include limitations.

---

## Missing Ingredients Should Not Always Block Meals

A small missing ingredient should not cancel an otherwise possible meal.

The system should reason by ingredient roles:

```text
base
protein
vegetable
flavour
sauce
fat
side
```

If the role is covered by another ingredient, the meal may still be possible.

---

# Long-Term Signal Vision

The ideal future planning layer can help the agent reason like this:

```text
This meal is possible from current inventory.
It uses a food that expires soon.
It avoids repeating the user's recent meals.
It has a reasonable protein opportunity.
It uses ingredients already available, so it is likely budget-friendly.
A missing vegetable can be replaced with frozen vegetables.
The data is incomplete, so the agent should phrase this as a flexible suggestion.
Logging it with inventory deduction would require user confirmation.
```

That is the kind of signal intelligence that will make the MCP server valuable to an agent.

---

# Final Philosophy

The best planning response schema is not the one with the most signals.

It is the one that helps the agent make better recommendations under uncertainty.

The schema should optimize for:

```text
grounded evidence
safe interpretation
user-fit awareness
imperfect-data tolerance
flexible substitutions
soft nutrition opportunities
goal-aware planning
cost and enjoyment awareness
clear action boundaries
```

Version 1.5A should build the foundation.

Later Version 1.5 stages can gradually turn those signals into stronger recommendation tools.
