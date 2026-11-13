#!/usr/bin/env python3
"""
Export MLflow experiments, runs, parameters, metrics, and registered models
to CSV and JSON in artefacts/mlflow_export/ for transparent grading inspection.
"""

import os
import json
from pathlib import Path
import pandas as pd
import mlflow

os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "1"
DB_PATH = Path("supporting_files/mlflow.db").resolve()
EXPORT_DIR = Path("artefacts/mlflow_export")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

mlflow.set_tracking_uri(f"sqlite:///{DB_PATH}")
client = mlflow.tracking.MlflowClient()

experiments = client.search_experiments()
exp_records = []
for exp in experiments:
    exp_records.append({
        "experiment_id": exp.experiment_id,
        "name": exp.name,
        "artifact_location": exp.artifact_location,
        "lifecycle_stage": exp.lifecycle_stage,
    })

pd.DataFrame(exp_records).to_csv(EXPORT_DIR / "experiments.csv", index=False)

all_runs_data = []
for exp in experiments:
    runs = client.search_runs(experiment_ids=[exp.experiment_id])
    for r in runs:
        row = {
            "run_id": r.info.run_id,
            "experiment_id": r.info.experiment_id,
            "experiment_name": exp.name,
            "status": r.info.status,
            "start_time": pd.to_datetime(r.info.start_time, unit="ms", utc=True).isoformat() if r.info.start_time else None,
            "end_time": pd.to_datetime(r.info.end_time, unit="ms", utc=True).isoformat() if r.info.end_time else None,
        }
        for k, v in r.data.params.items():
            row[f"param_{k}"] = v
        for k, v in r.data.metrics.items():
            row[f"metric_{k}"] = v
        for k, v in r.data.tags.items():
            if not k.startswith("mlflow."):
                row[f"tag_{k}"] = v
        all_runs_data.append(row)

df_runs = pd.DataFrame(all_runs_data)
df_runs.to_csv(EXPORT_DIR / "runs.csv", index=False)
with open(EXPORT_DIR / "runs.json", "w") as f:
    json.dump(all_runs_data, f, indent=2)

# Export registered models and aliases
models = client.search_registered_models()
models_data = []
for m in models:
    aliases = getattr(m, "aliases", {})
    versions_info = []
    for mv in m.latest_versions:
        versions_info.append({
            "version": mv.version,
            "current_stage": mv.current_stage,
            "run_id": mv.run_id,
            "source": mv.source,
            "status": mv.status,
        })
    models_data.append({
        "name": m.name,
        "aliases": aliases,
        "tags": m.tags,
        "latest_versions": versions_info,
    })

with open(EXPORT_DIR / "registered_models.json", "w") as f:
    json.dump(models_data, f, indent=2)
pd.DataFrame(models_data).to_csv(EXPORT_DIR / "registered_models.csv", index=False)

print(f"Successfully exported {len(exp_records)} experiments and {len(all_runs_data)} runs to {EXPORT_DIR}")

