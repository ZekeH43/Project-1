"""Exercise the documented entry point and its outputs from another directory."""

import json
import os
import subprocess
import sys

import pandas as pd
import pytest

from risk_reward.data import ROOT


def run_cli(directory, *args):
    return subprocess.run(
        [sys.executable, "-m", "risk_reward", *args],
        cwd=directory,
        env={**os.environ, "PYTHONPATH": str(ROOT), "MPLBACKEND": "Agg"},
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_cli_writes_traceable_results_and_plots(tmp_path):
    output = tmp_path / "results"
    completed = run_cli(
        tmp_path,
        "--tickers",
        "NVDA",
        "PFE",
        "--weights",
        "0.5",
        "0.5",
        "--years",
        "1",
        "3",
        "--simulations",
        "20",
        "--plots",
        "--output",
        str(output),
    )
    assert completed.returncode == 0, completed.stderr
    metadata = json.loads((output / "metadata.json").read_text())
    assert metadata["tickers"] == ["NVDA", "PFE"]
    assert metadata["weights"] == [0.5, 0.5]
    assert metadata["fitting_window"]["end"] == "2023-11-01"
    assert all(len(source["sha256"]) == 64 for source in metadata["sources"])
    summary = pd.read_csv(output / "summary.csv")
    assert summary.years.tolist() == [1, 3]
    for name in ("paths.png", "distribution.png"):
        assert (output / name).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.parametrize(
    "args",
    [
        ("--tickers", "NTES"),
        ("--years", "0"),
        ("--simulations", "0"),
        ("--weights", "1.1"),
        ("--investment", "nan"),
    ],
)
def test_invalid_cli_input_has_clear_errors(tmp_path, args):
    completed = run_cli(tmp_path, *args)
    assert completed.returncode == 2
    assert "error:" in completed.stderr and "Traceback" not in completed.stderr
    assert not (tmp_path / "artifacts").exists()
