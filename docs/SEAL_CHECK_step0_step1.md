# SEAL Check - Step0/Step1

Date: 2026-02-18  
Checked commit: `0b7f9100b360408023ff78d8195bb78ebb1de659`

## 0) Verdict

`PASS`

Reason:
1. Environment dependency baseline exists (`requirements.txt`) and runtime now records key versions
   (`torch`, `transformers`, etc.) to `env_versions.json`.
2. Smoke script exists and latest run is successful with complete artifacts.
3. Config validation chain exists and Step6/Step7 core configs are executable; one seed drift key
   was fixed to canonical form.

---

## 1) Step0 - Environment and dependency gate

### Status
`PASS`

### Evidence

- Dependency baseline exists and pinned:
  - `requirements.txt:1` to `requirements.txt:11`
- Setup path uses `requirements.txt`:
  - `README.md:10` to `README.md:11`
- Lock/conda files are not present in repo root (preflight command evidence):
  - `requirements.lock=False`, `environment.yml=False`, `pyproject.toml=False`, `poetry.lock=False`
- Runtime version snapshot now written by code:
  - writer function: `src/finder_rag/utils.py:44` to `src/finder_rag/utils.py:70`
  - smoke hook: `scripts/smoke.py:129` to `scripts/smoke.py:130`
  - step6 run hook: `scripts/run_experiment.py:94` to `scripts/run_experiment.py:95`
  - validate hook: `scripts/validate_config.py:38` to `scripts/validate_config.py:39`
  - matrix parent hook: `scripts/run_matrix_step6.py:81`
- Runtime evidence:
  - `outputs/a2_smoke_step0_step1/logs.txt:4` (`env_versions_path=...`)
  - `outputs/a2_smoke_step0_step1/env_versions.json:10` (`torch`)
  - `outputs/a2_smoke_step0_step1/env_versions.json:11` (`transformers`)

### Minimal repair patch (applied)

```diff
diff --git a/src/finder_rag/utils.py b/src/finder_rag/utils.py
@@
+def collect_env_versions(packages: Optional[Iterable[str]] = None) -> Dict[str, str]:
+    ...
+
+def write_env_versions(run_dir: str, packages: Optional[Iterable[str]] = None) -> str:
+    ...
diff --git a/scripts/smoke.py b/scripts/smoke.py
@@
-from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash
+from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash, write_env_versions
@@
+    env_path = write_env_versions(run_dir)
+    logger.info("env_versions_path=%s", env_path)
diff --git a/scripts/run_experiment.py b/scripts/run_experiment.py
@@
-from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash
+from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash, write_env_versions
@@
+    env_path = write_env_versions(run_dir)
+    logger.info("env_versions_path=%s", env_path)
diff --git a/scripts/validate_config.py b/scripts/validate_config.py
@@
-from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash
+from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash, write_env_versions
@@
+    env_path = write_env_versions(run_dir)
+    logger.info("env_versions_path=%s", env_path)
diff --git a/scripts/run_matrix_step6.py b/scripts/run_matrix_step6.py
@@
-from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash
+from finder_rag.utils import ensure_dir, generate_run_id, get_git_hash, write_env_versions
@@
+    write_env_versions(matrix_dir)
```

### Verification command

```powershell
python scripts/smoke.py --config configs/smoke.yaml --run-id a2_smoke_step0_step1
```

Expected output snippets:
- `outputs/a2_smoke_step0_step1/logs.txt:3` contains `seed=... git_hash=...`
- `outputs/a2_smoke_step0_step1/logs.txt:4` contains `env_versions_path=...`
- `outputs/a2_smoke_step0_step1/env_versions.json` contains `torch` and `transformers`

---

## 2) Step1 - Smoke/test gate

### Status
`PASS`

### Evidence

- Smoke entry exists:
  - `README.md:23`
  - `scripts/smoke.py:25` to `scripts/smoke.py:34`
- Smoke writes reproducibility artifacts:
  - `scripts/smoke.py:187` to `scripts/smoke.py:192`
- Latest smoke run successful:
  - `outputs/a2_smoke_step0_step1/logs.txt:7` metrics present
  - `outputs/a2_smoke_step0_step1/logs.txt:8` run_dir present
  - files exist:
    - `outputs/a2_smoke_step0_step1/config.yaml`
    - `outputs/a2_smoke_step0_step1/metrics.json`
    - `outputs/a2_smoke_step0_step1/logs.txt`
    - `outputs/a2_smoke_step0_step1/env_versions.json`

### Minimal repair patch

No additional patch required for smoke pass criteria after Step0 patch.

### Verification command

```powershell
Get-ChildItem outputs/a2_smoke_step0_step1 | Select Name
```

Expected output names:
- `config.yaml`
- `metrics.json`
- `logs.txt`
- `env_versions.json`

---

## 3) Config validation gate (Step6/Step7 related keys)

### Status
`PASS`

### Evidence

#### 3.1 Step6 schema validation exists and passes

- Validator exists and writes resolved config + issues:
  - `scripts/validate_config.py:13`
  - `scripts/validate_config.py:41` to `scripts/validate_config.py:50`
- Step6 base validation run:
  - `outputs/20260217_162501_5efb32/logs.txt:5` resolved config path
  - `outputs/20260217_162501_5efb32/logs.txt:6` `issues=none`
- Step6 base key coverage (complex/abbrev/numeric subsets):
  - `configs/step6_base.yaml:67` to `configs/step6_base.yaml:69`

#### 3.2 Drift key fix (seed key)

- Problem source (pre-fix): legacy top-level `seed` in eval config:
  - `configs/eval_numeric.yaml` old form used `seed` (now replaced)
- Canonical fix applied:
  - `configs/eval_numeric.yaml:8` to `configs/eval_numeric.yaml:9` (`runtime.seed`)
- Compatibility mapping added (prevents silent no-op for legacy files):
  - `src/config/schema.py:219` to `src/config/schema.py:223`
- Post-fix validation evidence:
  - `outputs/20260217_162815_f586d0/logs.txt:6` `issues=none`
  - `outputs/20260217_162815_f586d0/config.resolved.yaml:80` to
    `outputs/20260217_162815_f586d0/config.resolved.yaml:81` (`runtime.seed: 42`)

#### 3.3 Step7 configs are executable

- `make_tables` consumes `run_id/label/group` fields:
  - `scripts/make_tables.py:45` to `scripts/make_tables.py:48`
- Seal experiments config provides those fields:
  - `configs/step6_experiments_seal.yaml:2` to `configs/step6_experiments_seal.yaml:4`
- Plot config is executable with current step7 inputs:
  - command log: `outputs/20260217_162648_133004/logs.txt:1`
  - experiments loaded: `outputs/20260217_162648_133004/logs.txt:5`
  - enabled figure has data: `outputs/20260217_162648_133004/logs.txt:8`

### Minimal repair patch (applied)

```diff
diff --git a/src/config/schema.py b/src/config/schema.py
@@
+    if "seed" in raw:
+        try:
+            set_path(resolved, "runtime.seed", int(raw.get("seed")))
+        except (TypeError, ValueError):
+            pass
diff --git a/configs/eval_numeric.yaml b/configs/eval_numeric.yaml
@@
-seed: 42
+runtime:
+  seed: 42
```

### Verification commands

```powershell
python scripts/validate_config.py --config configs/step6_base.yaml --output-dir outputs
python scripts/validate_config.py --config configs/eval_numeric.yaml --output-dir outputs
python scripts/plot_all.py --config scripts/plot_config.yaml
```

Expected snippets:
- validate logs contain `issues=none`
- plot logs contain `experiments_loaded=10`
- plot logs contain `figure_written ... has_data=True`

---

## 4) Residual risk (non-blocking)

1. No lockfile/conda export is committed (only `requirements.txt` is present).
   Current mitigation is run-level `env_versions.json`, but strict byte-level
   reproducibility still benefits from an explicit lock file.
