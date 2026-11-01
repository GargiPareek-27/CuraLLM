"""Read-only inspection of candidate SFT datasets for CuraLLM.

For each candidate dataset this prints the schema, row count, a few sample rows,
text-length statistics, and counts of empty and duplicate values, then writes
reports/data_inspection.json. It never modifies or filters the data: its only
job is to show what is really in the data before any cleaning code is written.

Run from the repo root:  python ml/data/inspect_datasets.py
"""
import hashlib
import json
import sys
from pathlib import Path

# (label, Hugging Face dataset id, config name or None, split)
# These ids have NOT all been verified on the Hub. A failed load is reported
# in the output and the report, not hidden.
CANDIDATES = [
    ("chatdoctor_healthcaremagic", "lavita/ChatDoctor-HealthCareMagic-100k", None, "train"),
    ("medical_meadow_wikidoc", "medalpaca/medical_meadow_wikidoc", None, "train"),
    ("pubmedqa_labeled", "qiaojin/PubMedQA", "pqa_labeled", "train"),
]

SAMPLE_ROWS = 3
SAMPLE_CHARS = 300


def _as_text(value):
    """Return a string for any cell value (nested values become JSON text)."""
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, default=str, ensure_ascii=False)


def _percentile(sorted_values, q):
    if not sorted_values:
        return None
    index = min(len(sorted_values) - 1, int(q * len(sorted_values)))
    return sorted_values[index]


def summarize(rows):
    """Summarize a list of dict rows. Pure function, no I/O."""
    n_rows = len(rows)
    summary = {"n_rows": n_rows, "columns": [], "per_column": {}, "exact_duplicate_rows": 0}
    if n_rows == 0:
        return summary

    columns = list(rows[0].keys())
    summary["columns"] = columns

    for col in columns:
        texts = [_as_text(row.get(col)) for row in rows]
        lengths = sorted(len(t) for t in texts)
        summary["per_column"][col] = {
            "empty_or_whitespace": sum(1 for t in texts if not t.strip()),
            "distinct_values": len(set(texts)),
            "duplicate_values": n_rows - len(set(texts)),
            "chars_mean": round(sum(lengths) / n_rows, 1),
            "chars_median": _percentile(lengths, 0.5),
            "chars_p95": _percentile(lengths, 0.95),
            "chars_max": lengths[-1],
        }

    row_hashes = {
        hashlib.sha256(
            json.dumps(row, sort_keys=True, default=str, ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        for row in rows
    }
    summary["exact_duplicate_rows"] = n_rows - len(row_hashes)
    return summary


def _print_summary(summary, rows):
    print(f"rows: {summary['n_rows']} | columns: {summary['columns']}")
    print(f"exact duplicate rows: {summary['exact_duplicate_rows']}")
    for col, stats in summary["per_column"].items():
        print(f"  [{col}] {stats}")
    for i, row in enumerate(rows[:SAMPLE_ROWS]):
        print(f"--- sample row {i} ---")
        for key, value in row.items():
            print(f"  {key}: {_as_text(value)[:SAMPLE_CHARS]!r}")


def main():
    from importlib.metadata import version

    from datasets import load_dataset

    report = {
        "python": sys.version.split()[0],
        "datasets_version": version("datasets"),
        "results": {},
    }

    for label, hf_id, config, split in CANDIDATES:
        print(f"\n=== {label}: {hf_id} (config={config}, split={split}) ===")
        try:
            dataset = load_dataset(hf_id, config, split=split)
        except Exception as error:  # report every failure, hide nothing
            message = f"{type(error).__name__}: {str(error)[:300]}"
            print("LOAD FAILED:", message)
            report["results"][label] = {"hf_id": hf_id, "load_error": message}
            continue

        rows = dataset.to_list()
        summary = summarize(rows)
        _print_summary(summary, rows)
        report["results"][label] = {"hf_id": hf_id, "config": config, "split": split, **summary}

    out_path = Path("reports") / "data_inspection.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
