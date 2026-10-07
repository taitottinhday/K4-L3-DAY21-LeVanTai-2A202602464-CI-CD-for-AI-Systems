"""Back up the already appended dataset, then restore the lab's batch-1 baseline."""

from pathlib import Path
import shutil

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    train_path = ROOT / "data/train_batch1.csv"
    data = pd.read_csv(train_path)
    batch2 = pd.read_csv(ROOT / "data/train_batch2.csv")
    if len(data) == 22361:
        print("Step 2 baseline already prepared")
        return
    assert len(data) == 44722 and len(batch2) == 22361
    assert data.tail(len(batch2)).reset_index(drop=True).equals(batch2)
    backup = ROOT.parent / "aws-cli-session/train-full-44722.csv"
    if not backup.exists():
        shutil.copyfile(train_path, backup)
    data.iloc[:22361].to_csv(train_path, index=False)
    print(f"Preserved full dataset in {backup}; prepared 22,361 baseline rows")


if __name__ == "__main__":
    main()
