# Historical data and provenance

The runnable examples use the existing files in `Resources csv/`. No source price CSV was changed during the refactor. They are historical snapshots, not current quotes.

## Available files

These counts and dates were read from the committed CSVs. The filenames identify the symbols; the repository does not provide a verified security-identifier mapping.

| Symbol | Price observations | Earliest date | Latest date |
| --- | ---: | --- | --- |
| AOSL | 1,257 | 2018-11-02 | 2023-11-01 |
| ARCT | 1,257 | 2018-11-02 | 2023-11-01 |
| BMY | 1,257 | 2018-11-02 | 2023-11-01 |
| DELL | 1,225 | 2018-12-20 | 2023-11-01 |
| EBIX | 1,257 | 2018-11-02 | 2023-11-01 |
| INMD | 1,067 | 2019-08-08 | 2023-11-01 |
| MRK | 1,257 | 2018-11-02 | 2023-11-01 |
| NETTF | 721 | 2020-12-21 | 2023-11-01 |
| NVDA | 1,257 | 2018-11-02 | 2023-11-01 |
| PFE | 1,257 | 2018-11-02 | 2023-11-01 |
| SCYX | 1,257 | 2018-11-02 | 2023-11-01 |
| VZ | 1,257 | 2018-11-02 | 2023-11-01 |

There is **no NTES CSV**. The corresponding notebook explicitly skips calculation. NETTF and NTES are distinct symbols, so substituting NETTF would mislabel the result. The CLI reports available files when a requested symbol is missing.

## File contract

Each file is named `<TICKER>_data.csv`. Two columns are required:

| Column | Accepted format | Use |
| --- | --- | --- |
| `Date` | `MM/DD/YYYY` | Observation date; must be present and unique |
| `Close/Last` | Positive finite number, optionally with `$`, commas, or whitespace | Closing-price input |

The existing files also contain `Volume`, `Open`, `High`, and `Low`. These columns are unused. An `N/A` volume does not invalidate an otherwise valid close.

The loader sorts the originally newest-first rows into chronological order. It rejects missing, nonnumeric, nonpositive, or infinite closes and duplicate dates. At least three price observations are needed to estimate a sample covariance from two returns.

For multiple assets, an inner join retains only common observed dates. It never fills missing prices. The run metadata distinguishes each file's original window from the shorter common fitting window. The code does not verify an exchange calendar: a return between adjacent retained observations can span more than one market session, yet the model treats it as one step. This matters especially for sparse histories.

## Known provenance gaps

The original project referenced several external data APIs, but it did not record a definitive publisher, retrieval timestamp, dataset version, redistribution license, or adjustment policy for every CSV. The refactor cannot establish those facts from the files alone. It makes no new license or verified market-data claim.

Splits, dividends, ticker changes, stale observations, and missing sessions have not been independently reconciled. The original narrative already raised a possible corporate-action concern for SCYX; the refactor preserves the source values and does not treat that narrative as a verified adjustment record. Extreme changes in any input can distort estimated means and covariance.

To improve the dataset, obtain documented price histories, confirm their permitted use and adjustment convention, record stable identifiers and download dates, and add calendar/corporate-action checks. Keep the existing snapshot for reproducibility rather than silently overwriting it.

## Reproduce an output

Every CLI run writes `metadata.json` containing:

- SHA-256 hashes, row counts, and date ranges for each complete source file.
- Ordered tickers, weights, horizons, simulations, seed, and initial value.
- The aligned fitting window, model identifier, assumptions, and dependency versions.

Hashes establish whether the input bytes match; they do not certify the data's accuracy. See the committed [example metadata](../reports/example/metadata.json).

## Historical artifacts

`Data_1.csv`, `Book1.xlsx`, and `Risk & Reward.pptx` preserve material from the original experiment. They are not read by the current analysis, and their numbers and recommendations have not been revalidated. In particular, the old summary's “average” should not be assumed to be an actual mean of simulated outcomes.

`Book1.csv`, `Data_1_Analysis.csv`, and `Data_1_Analysis_with_graphs.csv` were byte-identical to `Data_1.csv` and were removed as duplicates. The current output lives in `summary.csv` and explicitly separates means, medians, and quantiles.
