import pandas as pd
df = pd.read_csv("data/train.csv", header=None, names=["label","title","description"])
CANON = r"#\d{2,4};|\b(?:lt|gt|quot|amp|nbsp|apos);"
RETYPED = r"#\d{2,4};|(?:lt|gt|quot|amp|nbsp|apos);"
for strip in (True, False):
    t = df["title"].astype(str); d = df["description"].astype(str)
    if strip: t, d = t.str.strip(), d.str.strip()
    text = t + " " + d
    for name, pat in (("canonical", CANON), ("retyped", RETYPED)):
        print(f"strip={strip!s:5} {name:9} {int(text.str.contains(pat, regex=True).sum())}")