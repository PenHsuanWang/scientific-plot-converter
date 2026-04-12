## PR Summary

> Implements the standard plot format (typography, Petroff palette, golden margins, and auto-rotation) according to US-2.x requirements.

Closes #1

---

## Type of Change

<!-- Check all that apply -->
- [x] ✨ New feature (non-breaking addition)
- [ ] 🐛 Bug fix
- [x] 🎨 Visual / styling fix
- [ ] 📝 Documentation update
- [ ] ♻️ Refactor (no behaviour change)
- [x] 🧪 Test improvement
- [ ] 🔧 CI / tooling change

---

## SRS / Requirements Reference

- US-2.1 Scenario 1 — scientific authority typography
- US-2.2 Scenario 1 — three-tier header typography (Tier-1 bold, Tier-2 italic, Tier-3 right)
- US-2.4 Scenario 4 — X-axis tick label auto-rotation
- US-2.5 Scenario 1 — Petroff-compliant color palette
- US-2.6 — axis typography quantification (sizes, padding, and golden margins)

---

## What Changed

- `src/dsprinter/render/engine.py` — Configured matplotlib `rcParams` for golden margins, Petroff palette, and typography sizes.
- `src/dsprinter/render/plots.py` — Implemented three-tier header logic and axis formatting (auto-rotation, tick parameters).
- `tests/test_engine.py` — Added unit tests verifying fonts, font sizes, margins, and palette configurations.

---

## Testing Checklist

- [x] `tox` passes locally (all lint + test jobs green)
- [x] New unit tests added for every new behaviour / bug fix
- [x] No regression in existing 109 tests
- [x] `dp hist1d --help` and `dp trend --help` still produce correct output

---

## Visual Output Checklist _(for plot/engine changes only)_

- [x] Sample PDF regenerated: `dp hist1d --input demo_histogram_data.csv --x Tool_A_CD --project "Test" --status "Draft" --context "N=200" --output figure_out/check.pdf`
- [x] Three-tier typography (Tier-1 bold top-left, Tier-2 italic, Tier-3 right) visible and legible
- [x] Font sizes match US-2.6 table (axis title 12 pt, tick labels 10 pt, Tier-1 14 pt)
- [x] Tick labels do not overlap; auto-rotation fires correctly for long labels
- [x] Golden margins are respected (no axis labels clipped)
- [x] Petroff palette applied (no rainbow / high-saturation colours)

---

## Documentation Checklist

- [x] Public function / class docstrings updated for changed APIs
- [x] `DSPrinter_SRS.md` updated if acceptance criteria changed
- [x] `README.md` updated if CLI flags or output format changed
- [x] Sphinx docs build cleanly: `sphinx-build -b html docs docs/_build/html`

---

## Reviewer Notes

Please review the visual output using the sample PDF generated in `figure_out/check.pdf` to ensure the layout strictly meets the standard plot format requirements.
