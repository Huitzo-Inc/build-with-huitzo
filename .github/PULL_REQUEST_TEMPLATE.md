## What and why

Briefly: what does this change and which rung does it touch?

## Checklist

- [ ] Deterministic Python owns the decisions; the model is augmentation only
- [ ] No model name appears in pack code (uses `ctx.llm.complete(..., profile=...)`)
- [ ] Input and output are typed Pydantic models
- [ ] Tests run offline and pass (`pytest -q`)
- [ ] If I changed any English `.md`, I re-translated and ran `python scripts/check_i18n_staleness.py --fix`
- [ ] Public copy has no em-dashes and no internal jargon
