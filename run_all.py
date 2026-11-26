"""Rebuild every table, report and chart in output/ from the data in data/.

Order matters: the turkey model feeds the price index, which feeds everything else.
Each script's console report is saved next to its outputs.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
STEPS = [
    ("turkey_nowcast_ml_ensemble.py", "turkey_nowcast_ml_ensemble_report.txt"),
    ("build_index.py", "report.txt"),
    ("affordability.py", "affordability_report.txt"),
    ("by_income.py", "by_income_report.txt"),
    ("deep_dive.py", "deep_dive_report.txt"),
]

for script, report in STEPS:
    print(f"Running {script} ...", flush=True)
    result = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT,
                            capture_output=True, text=True)
    (ROOT / "output" / report).write_text(result.stdout)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        sys.exit(f"{script} failed")
print("Done. Outputs are in output/.")
