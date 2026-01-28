# AGENTS

## Code style
- Python: follow PEP 8, keep lines <= 100 chars, prefer explicit names.
- Use type hints for public functions when reasonable.
- Keep modules small and focused; avoid hidden side effects.

## Logging
- Use `logging` (not print) in scripts.
- Every run writes logs to `outputs/<run_id>/logs.txt`.
- Log the command line, config path, and key run parameters.

## Reproducibility rules
- Every experiment MUST write:
  - `config.yaml`
  - random seed
  - git commit hash (or "unknown")
  - metrics
  to `outputs/<run_id>/`.
- Set random seeds for `random` and `numpy`.

## Data policy
- Do NOT commit full dataset files.
- Large data belongs in `data/` or `dataset/` and should be git-ignored.

## Execution policy
- Always run the smoke test before any experiment.
