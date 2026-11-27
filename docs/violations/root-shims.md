# Deviation: root modules removed

Per migration-plan S53, root `calculator.py` and `task_runner.py` have been
**removed** rather than kept as 5-line shims. All imports use `src.calc.*`
(public re-exports from `src/calc/__init__.py`); entrypoints are `python main.py`
and `python main.py --worker [N]` (root `main.py`) and `python src/main.py`.
