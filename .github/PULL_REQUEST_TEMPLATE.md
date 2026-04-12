## PR Summary

> _One-sentence description of what this PR does._

Closes #<!-- issue number -->

---

## Type of Change

<!-- Check all that apply -->
- [ ] ✨ New feature (non-breaking addition)
- [ ] 🐛 Bug fix
- [ ] 🎨 Visual / styling fix
- [ ] 📝 Documentation update
- [ ] ♻️ Refactor (no behaviour change)
- [ ] 🧪 Test improvement
- [ ] 🔧 CI / tooling change

---

## SRS / Requirements Reference

<!-- List every User Story acceptance criterion addressed, e.g.: -->
<!-- - US-2.1 Scenario 2 — consistent typography -->
<!-- - US-2.6 — axis typography quantification -->

-

---

## What Changed

<!-- Bullet list of the key files and what was changed in each -->
- `src/dsprinter/render/engine.py` —
- `src/dsprinter/render/plots.py` —
- `tests/` —

---

## Testing Checklist

- [ ] `tox` passes locally (all lint + test jobs green)
- [ ] New unit tests added for every new behaviour / bug fix
- [ ] No regression in existing 109 tests
- [ ] `dp hist1d --help` and `dp trend --help` still produce correct output

---

## Visual Output Checklist _(for plot/engine changes only)_

- [ ] Sample PDF regenerated: `dp hist1d --input demo_histogram_data.csv --x Tool_A_CD --project "Test" --status "Draft" --context "N=200" --output figure_out/check.pdf`
- [ ] Three-tier typography (Tier-1 bold top-left, Tier-2 italic, Tier-3 right) visible and legible
- [ ] Font sizes match US-2.6 table (axis title 12 pt, tick labels 10 pt, Tier-1 14 pt)
- [ ] Tick labels do not overlap; auto-rotation fires correctly for long labels
- [ ] Golden margins are respected (no axis labels clipped)
- [ ] Petroff palette applied (no rainbow / high-saturation colours)

---

## Documentation Checklist

- [ ] Public function / class docstrings updated for changed APIs
- [ ] `DSPrinter_SRS.md` updated if acceptance criteria changed
- [ ] `README.md` updated if CLI flags or output format changed
- [ ] Sphinx docs build cleanly: `sphinx-build -b html docs docs/_build/html`

---

## Reviewer Notes

<!-- Anything the reviewer should pay special attention to, known limitations, or follow-up issues to open -->
