
import re
import pandas as pd
from src.load import load_corpus
#from src.clean import repair, CORRUPT
from collections import Counter
from src.load import load_corpus
from src.clean import PATTERNS, CORRUPT

df = load_corpus()
for name, p in PATTERNS.items():
    print(name, df["text"].str.contains(p, regex=True).sum())

any_hit = df["text"].str.contains(CORRUPT, regex=True)
print("any:", any_hit.sum(), any_hit.mean().round(4))
print(df.groupby("label")["text"].apply(
    lambda s: s.str.contains(CORRUPT).mean()).round(4))
print(df["text"].str.contains(r"(?<!&)#39;").sum())

