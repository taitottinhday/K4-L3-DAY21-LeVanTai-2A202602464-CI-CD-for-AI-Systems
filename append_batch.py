import pandas as pd

df_train = pd.read_csv("data/train_batch1.csv")
df_new   = pd.read_csv("data/train_batch2.csv")

original_size = len(df_train)
if len(df_train) == 2 * len(df_new) and df_train.tail(len(df_new)).reset_index(drop=True).equals(df_new):
    print(f"Batch 2 da duoc ghep: {original_size} mau (khong ghep trung).")
elif len(df_train) == len(df_new):
    df_updated = pd.concat([df_train, df_new], ignore_index=True)
    df_updated.to_csv("data/train_batch1.csv", index=False)
    print(f"Cap nhat du lieu: {original_size} -> {len(df_updated)} mau")
else:
    raise SystemExit("Dataset size is unexpected. Check the batches before appending.")
