# Reproducible example output

[summary.csv](summary.csv) and [metadata.json](metadata.json) were generated with:

```bash
python -m risk_reward --tickers NVDA PFE --weights 0.5 0.5 --years 1 3 5 --investment 15000 --output reports/example
```

Run from the repository root with the dependencies in `requirements.txt`. This overwrites these two example files; use `--output artifacts/example` for an untracked comparison instead. Add `--plots` to generate preview charts for the first horizon.

The example uses 500 paths, seed 42, and 1,257 shared observations from November 2, 2018 through November 1, 2023. The metadata records the exact input hashes and environment versions. Small numerical differences can occur across numerical libraries or platforms.

These files demonstrate traceable program output. Their growth factors, terminal values, and loss fractions describe the fitted model, not expected investment performance. The inputs' split/dividend adjustment policy is unverified, and the 2.5th/97.5th percentiles are scenario quantiles rather than guaranteed future probabilities. Read [MODEL.md](../../docs/MODEL.md) and [DATA.md](../../docs/DATA.md) before interpreting the numbers.
