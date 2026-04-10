import json
import sys
import tempfile
from pathlib import Path


def main():
    # Grab the IDs passed in the terminal
    target_ids = set(sys.argv[1:])
    if not target_ids:
        print("Usage: python tools/ground-truth-labeler/subset_gt.py gt-022 gt-023 ...")
        sys.exit(1)

    # Path to the canonical GT file (assumes running from repo root)
    gt_path = Path("agents/eval/extraction_ground_truth.json")

    if not gt_path.exists():
        print(f"❌ Error: Could not find {gt_path}.")
        print("Make sure you are running this script from the repository root.")
        sys.exit(1)

    with open(gt_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Filter for only your assigned IDs
    subset = [record for record in data if record.get("ground_truth_id") in target_ids]

    if not subset:
        print(f"⚠️ Warning: No records found matching the IDs: {', '.join(target_ids)}")
        sys.exit(1)

    # OS-Agnostic Temporary File Generation
    temp_dir = Path(tempfile.gettempdir())
    out_path = temp_dir / "my_gt_subset.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(subset, f, indent=2, ensure_ascii=False)

    print(f"✅ Extracted {len(subset)} records to {out_path}")
    print(
        f'🚀 Next, run: python -m agents.eval.run_extraction_eval --mode pipeline --ground-truth "{out_path}" --no-artifacts'
    )


if __name__ == "__main__":
    main()
