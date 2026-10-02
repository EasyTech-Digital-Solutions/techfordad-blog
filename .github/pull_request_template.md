## What changed and why


## Before merging

- [ ] The **Tests** check is green (or `tests/run.sh` passes locally).
- [ ] If the **UI changed**, the tests changed with it (see `tests/README.md`, "When you change the UI"):
  - new kind of page → `tests/pages.py`
  - new section of `css/style.css` → `tests/data/ui_components.json` **and** a test that exercises it
  - new button, click behavior or print rule → a test in `tests/test_ui_interactions.py` or `tests/test_ui_print.py`
  - new Amazon link or offer → `tests/data/approved_amazon_links.json` and `python3 scripts/amazon_registry.py --update`
  - new third-party script, form or embed → `tests/data/third_party_hosts.json` (a deliberate privacy decision)
- [ ] The accessibility baseline (`tests/data/a11y_known_issues.json`) did not grow.
- [ ] After merging to `main`: `tests/run.sh --live` passes (or the live site was checked by hand).
