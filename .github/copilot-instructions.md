<!-- .github/copilot-instructions.md for Project-1-Unibot -->
# Copilot / AI agent instructions — Project-1-Unibot

This file gives concise, actionable guidance for an automated coding agent working on the Unibot mini-project. Keep edits minimal and follow the project's lightweight style.

Overview
- Small Python prototype that reads a CSV dataset (Data/Unilife.csv) and runs quick data-processing helper scripts.
- There are three step files in the repo root that demonstrate focused utilities:
  - `Unibot_step1.py` — CSV load + basic column cleanup using pandas
  - `Unibot_step2.py` — Event-date parsing and sorting using regex and a month mapping
  - `Unibot_step3.py` — Simple keyword-based text classifier (studying / sports / social)

Quick architecture and data flow
- Data lives in `Data/Unilife.csv`. Each step script reads it directly via a relative path.
- Scripts are small, single-file utilities (no package/module structure). Treat them as scripts rather than importable libraries unless refactoring into modules.
- Typical flow: read CSV → normalize/clean columns → apply parsing or classification → print results.

Project-specific patterns and conventions
- File paths use lowercase `data/unilife.csv` in code; on Windows the workspace path uses `Data/Unilife.csv`. Preserve relative paths but be cautious about case—tests and scripts expect `data/unilife.csv` (lowercase) so prefer that path when adding code.
- Minimal dependencies: the code uses only standard library + pandas. If you add packages, also add a `requirements.txt` with pinned versions.
- Keep changes small and well-scoped. The repository is a learning/prototype repo; avoid large infrastructure changes unless requested.
- Scripts print human-readable output directly (no CLI parsing). If adding CLI behavior, use `argparse` and keep defaults matching current script behavior.

Examples to reference in edits
- Normalizing CSV columns (from `Unibot_step1.py`):
  - Lowercase and strip column names then strip all string values: `df.columns = [c.strip().lower() for c in df.columns]` and `df[c] = df[c].astype(str).str.strip()`
- Date extraction pattern (from `Unibot_step2.py`):
  - Use two regex attempts to capture dates with/without parentheses and fallback values to push unknowns to the end: use `(\d{1,2})\s*([A-Za-z]+)` and a month-name map.
- Text classification (from `Unibot_step3.py`):
  - Keyword sets for categories, lowercase input, count keyword matches, require a unique top score, otherwise return `None`.

Developer workflows (how to run / debug)
- Run any step file with the system Python in a terminal: `python Unibot_step1.py` (on Windows Powershell use `python Unibot_step1.py`).
- If pandas is missing, install it locally with `pip install pandas` and add `pandas` to `requirements.txt`.
- There are no automated tests or build scripts. For quick checks, run the scripts and inspect stdout.

Integration points and risks
- External dependency: `pandas` for CSV handling. No external APIs or services are used.
- CSV path sensitivity: code expects a `data/unilife.csv` relative path. If a contributor renames the CSV or changes folders, update all three scripts.

When modifying code
- Preserve the small-script style or explicitly refactor into modules with corresponding tests.
- Add `requirements.txt` when introducing third-party packages.
- Write minimal smoke tests (small scripts or functions) that run quickly — this repo has example smoke-tests inside `Unibot_step3.py`.

Files to inspect first
- `Unibot_step1.py`, `Unibot_step2.py`, `Unibot_step3.py`, and `Data/Unilife.csv`.

If you need more context
- Ask the repo owner (project maintainer) whether they prefer `Data/Unilife.csv` vs `data/unilife.csv` as canonical path casing.

Feedback
- I added these concise instructions focused on discoverable, actionable patterns. If you'd like different scope (more examples, coding conventions, or a checklist for PRs), tell me what to expand.
