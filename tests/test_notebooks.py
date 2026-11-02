"""Prevent the copied-ticker mistakes found in the original notebooks."""

import ast
import json

from risk_reward.data import ROOT


def test_single_stock_notebook_labels_match_the_requested_ticker():
    checked = 0
    for path in ROOT.glob("*.ipynb"):
        if path.stem in {"Risk_Simulator", "Simulation_Concepts"}:
            continue
        expected = path.stem.removesuffix("_1")
        cells = json.loads(path.read_text())["cells"]
        assignments = []
        for cell in cells:
            if cell["cell_type"] == "code":
                for node in ast.walk(ast.parse("".join(cell["source"]))):
                    if isinstance(node, ast.Assign) and any(
                        isinstance(target, ast.Name) and target.id == "TICKER"
                        for target in node.targets
                    ):
                        assignments.append(ast.literal_eval(node.value))
        assert assignments == [expected], path.name
        checked += 1
    assert checked == 12
