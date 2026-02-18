#!/usr/bin/env bash
set -euo pipefail

SMOKE_RUN_ID="${SMOKE_RUN_ID:-seal_final_smoke}"
BASE_CONFIG="${BASE_CONFIG:-configs/step6_base.yaml}"
MATRIX_CONFIG="${MATRIX_CONFIG:-configs/tmp_matrix_seal_pqe_only.yaml}"
EXPERIMENTS_CONFIG="${EXPERIMENTS_CONFIG:-configs/step6_experiments_seal.yaml}"
PLOT_CONFIG="${PLOT_CONFIG:-scripts/plot_config.yaml}"

echo "[seal] smoke_run_id=${SMOKE_RUN_ID}"
python scripts/smoke.py --config configs/smoke.yaml --run-id "${SMOKE_RUN_ID}"

MATRIX_OUTPUT="$(python scripts/run_matrix_step6.py --base-config "${BASE_CONFIG}" --matrix "${MATRIX_CONFIG}")"
echo "${MATRIX_OUTPUT}"
MATRIX_ID="$(printf '%s\n' "${MATRIX_OUTPUT}" | sed -n 's/^matrix_id=//p' | tail -n 1)"
if [[ -z "${MATRIX_ID}" ]]; then
  echo "[seal] ERROR: failed to parse matrix_id from run_matrix_step6 output" >&2
  exit 1
fi
echo "[seal] matrix_id=${MATRIX_ID}"

python scripts/make_tables.py --experiments "${EXPERIMENTS_CONFIG}"
python scripts/plot_all.py --config "${PLOT_CONFIG}"

echo "seal_final_smoke_run_id=${SMOKE_RUN_ID}"
echo "seal_final_matrix_id=${MATRIX_ID}"
