# Version 1.5 Documentation Management and Archive Recommendations

**Last updated:** 2026-05-19

---

## Active Documentation to Keep Updated

These files should remain active project documentation.

| File | Recommendation | Reason |
|---|---|---|
| `project_roadmap.md` | Keep active and replace with updated roadmap | This is the main high-level project direction. It should reflect that 1.5A, 1.5B, and 1.5C are complete and that 1.5D is next. |
| `version1_5_doc.md` | Keep active and replace with consolidated Version 1.5 document | This should be the main Version 1.5 overview/closeout document. The current file has useful content but needs markdown cleanup and consolidation. |
| `future_version_plans.md` | Keep active and replace with updated future plans | This is the correct home for 1.5D+, shopping-list drafts, feedback, learning, nutrition, cost, and waste-aware plans. |
| `future_learning_over_time_feedback_recommendations.md` | Keep as active future/reference planning document | This remains relevant for future feedback-aware recommendations and should not be discarded. |
| `v1_5_signal_vision_ideas_updated.md` | Keep as reference, or archive after summarising | This is valuable as a long-form vision document. Keep active if you want a deep signal reference; otherwise archive it after the key signal philosophy is captured in `version1_5_doc.md` and `future_version_plans.md`. |

---

## Files Recommended for Archive

These files are useful historically but should no longer be treated as active working docs.

| File | Suggested archive path | Reason |
|---|---|---|
| `v1_5_draft.md` | `docs/docs/archive/originals/v1_5_draft.md` | This is an earlier plan. It has been superseded because the sequence changed: meal suggestions now come before restock suggestions. |
| `v1_5a_proposal_plan_updated.md` | `docs/docs/archive/originals/v1_5a_proposal_plan_updated.md` | This was the proposal stage for 1.5A. The implementation is now complete and the core ideas are consolidated into the active Version 1.5 document. |
| `version_1_5a_implementation_notes.md` | `docs/docs/archive/originals/version_1_5a_implementation_notes.md` | This is a completed checkpoint note. Archive after confirming the active Version 1.5 document captures the 1.5A tool, architecture, and testing expectations. |
| `v1_5b_b_review_use_soon_items_patch.md` | `docs/docs/archive/originals/v1_5b_b_review_use_soon_items_patch.md` | This is a patch note for one focused tool. Archive after the active Version 1.5 document lists `review_use_soon_items`. |
| `v1_5b_c_review_inventory_data_quality_patch.md` | `docs/docs/archive/originals/v1_5b_c_review_inventory_data_quality_patch.md` | This is a patch note for one focused tool. Archive after the active Version 1.5 document lists `review_inventory_data_quality`. |

---

## Optional Archive Treatment

| File | Recommendation | Reason |
|---|---|---|
| `v1_5_signal_vision_ideas_updated.md` | Optional archive/reference | This is still valuable, but it is long and vision-oriented. If your docs folder is becoming cluttered, move it to archive/reference and keep only the shorter active summaries in `version1_5_doc.md` and `future_version_plans.md`. |

Suggested path if archiving it:

```text
docs/docs/archive/originals/v1_5_signal_vision_ideas_updated.md
```

---

## Suggested Git Move Commands

Adjust paths if these files currently live somewhere else.

```powershell
git mv docs/docs/v1_5_draft.md docs/docs/archive/originals/v1_5_draft.md
git mv docs/docs/v1_5a_proposal_plan_updated.md docs/docs/archive/originals/v1_5a_proposal_plan_updated.md
git mv docs/docs/version_1_5a_implementation_notes.md docs/docs/archive/originals/version_1_5a_implementation_notes.md
git mv docs/docs/v1_5b_b_review_use_soon_items_patch.md docs/docs/archive/originals/v1_5b_b_review_use_soon_items_patch.md
git mv docs/docs/v1_5b_c_review_inventory_data_quality_patch.md docs/docs/archive/originals/v1_5b_c_review_inventory_data_quality_patch.md
```

Optional:

```powershell
git mv docs/docs/v1_5_signal_vision_ideas_updated.md docs/docs/archive/originals/v1_5_signal_vision_ideas_updated.md
```

---

## Replacement Order

Recommended update order:

```text
1. Replace project_roadmap.md with the updated roadmap.
2. Replace version1_5_doc.md with the consolidated Version 1.5 document.
3. Replace future_version_plans.md with the updated future plan.
4. Move superseded proposal/patch notes to archive.
5. Run docs preview or inspect markdown rendering.
6. Run pytest -q once more if code files were untouched but you want a final confidence check.
7. Commit documentation closeout.
```

---

## Suggested Commit Message

```bash
git add .
git commit -m "Update v1.5 documentation and archive superseded planning notes"
```
