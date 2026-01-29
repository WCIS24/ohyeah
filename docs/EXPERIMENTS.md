# Experiments

## run_experiment

`run_experiment.py` is the single entry-point. It writes:
- `outputs/<run_id>/config.resolved.yaml`
- `outputs/<run_id>/config.yaml`
- `outputs/<run_id>/git_commit.txt`
- `outputs/<run_id>/summary.json`
- `outputs/<run_id>/metrics.json`

`summary.json` includes:
- `runs.*` : run_id of each sub-stage
- `metrics.*` : metrics from those sub-stages

## sweep

`sweep.py` runs a grid over parameters and writes:
- `outputs/<sweep_id>/leaderboard.csv`
- `outputs/<sweep_id>/best_config.yaml`

To export tables for the paper, use `make_tables.py` with an `experiments.yaml`
that lists each run_id and label.
