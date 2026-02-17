# Seal Traceability Spec (Step6 Matrix)

This project now enforces matrix-level traceability for Step6 runs.

## Expected output layout

```
outputs/<matrix_id>/
  matrix.json
  experiments_resolved.yaml
  runs/
    <run_id>/
      config.resolved.yaml
      config.yaml
      git_commit.txt
      logs.txt
      summary.json
      metrics.json
```

## What is recorded

- `matrix.json` records:
  - `matrix_id`, `created_at_utc`, `git_hash`
  - `base_config`, `matrix_config`, `matrix_dir`, `runs_root`
  - per-experiment command, overrides, run paths, key config summary
- `experiments_resolved.yaml` records:
  - per-experiment resolved run mapping with seed and key switches
  - retriever mode, multistep/calculator on-off, subset paths
- each child run logs:
  - command line
  - config path
  - git hash
  - seed
  - resolved config path

## Minimal verification command

```powershell
python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix outputs/tmp_matrix_min_trace.yaml
```

After run, verify:

- `outputs/<matrix_id>/matrix.json`
- `outputs/<matrix_id>/experiments_resolved.yaml`
- `outputs/<matrix_id>/runs/<run_id>/logs.txt` (contains git hash + seed + resolved config path)
