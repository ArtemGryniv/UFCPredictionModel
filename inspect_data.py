import pandas as pd

fights = pd.read_csv('data/ufc_fight_results.csv')

print("Shape:", fights.shape)
print("Columns:", fights.columns.tolist())
print(fights.head())

print(fights[["BOUT", "OUTCOME"]].head(10).to_string(index=False))

print("\nOutcome counts:")
print(fights["OUTCOME"].value_counts(dropna=False))