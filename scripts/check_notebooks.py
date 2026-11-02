"""Execute every project notebook with a fresh Jupyter kernel and save artifacts."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    """Use the same interpreter/environment as the caller, including on Windows."""
    notebooks = sorted(ROOT.glob("*.ipynb"))
    if not notebooks:
        raise SystemExit("No project notebooks found.")
    output = ROOT / "artifacts" / "notebooks"
    output.mkdir(parents=True, exist_ok=True)
    for notebook in notebooks:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "jupyter",
                "nbconvert",
                "--to",
                "notebook",
                "--execute",
                str(notebook),
                "--output-dir",
                str(output),
                "--ExecutePreprocessor.timeout=300",
            ],
            cwd=ROOT,
            check=True,
        )
    print(f"Executed {len(notebooks)} notebooks. NTES explicitly skips when its CSV is absent.")


if __name__ == "__main__":
    main()
