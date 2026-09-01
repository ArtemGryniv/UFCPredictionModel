# This file verifies csv files were downloaded correctly and cleans and merges the tables

import pandas as pd
from difflib import get_close_matches 

### Fights ###
fights = pd.read_csv('data/ufc_fight_results.csv')

print("fights data Shape:", fights.shape)
print("fights data Columns:", fights.columns.tolist())
print(fights.head())

print(fights[["BOUT", "OUTCOME"]].head(10).to_string(index=False))

print("\nOutcome counts:")
print(fights["OUTCOME"].value_counts(dropna=False))


### Events ###
events = pd.read_csv("data/ufc_event_details.csv")

print("\nEvent data shape:", events.shape)
print("Event data columns:", events.columns.tolist())

print(events.head(5).to_string(index=False))

print("\nDate type before conversion:", events["DATE"].dtype)

events["DATE"] = pd.to_datetime(events["DATE"])

print("Date type after conversion:", events["DATE"].dtype)


print("Before cleaning:", repr(fights.loc[0, "EVENT"]))

fights["EVENT"] = fights["EVENT"].str.strip()
events["EVENT"] = events["EVENT"].str.strip()

print("After cleaning:", repr(fights.loc[0, "EVENT"]))

# Two events had mismatched names accross dfs, so manually replace
event_name_corrections = {
    "UFC Fight Night: Lopes vs. Silva":
        "Noche UFC: Lopes vs. Silva",

    "UFC Fight Night: Grasso vs. Shevchenko 2":
        "Noche UFC: Grasso vs. Shevchenko 2"
}

fights["EVENT"] = fights["EVENT"].replace(event_name_corrections)

# One event was missing from events table, so manually add
missing_event = pd.DataFrame([
    {
        "EVENT": "UFC - Road to UFC 4.6",
        "URL": "http://ufcstats.com/event-details/8fbcd82bf7f352bf",
        "DATE": pd.Timestamp("2025-08-22"),
        "LOCATION": "Shanghai, Hebei, China"
    }
])

events = pd.concat(
    [events, missing_event],
    ignore_index=True
)

### merge Date and Location from events to fights df and clean ###

fights_with_events = fights.merge(
    events[["EVENT", "DATE", "LOCATION"]],
    on="EVENT",
    how="left",
    validate="many_to_one"
)

print("\nRows before merge:", len(fights))
print("Rows after merge:", len(fights_with_events))
print("Fights missing a date:", fights_with_events["DATE"].isna().sum())

print(
    fights_with_events[
        ["DATE", "EVENT", "BOUT", "OUTCOME"]
    ].head(10).to_string(index=False)
)

fights_clean = fights_with_events.copy()

fights_clean[["FIGHTER_A", "FIGHTER_B"]] = (
    fights_clean["BOUT"].str.split(
        " vs. ",
        n=1,
        expand=True
    )
)

fights_clean["FIGHTER_A"] = fights_clean["FIGHTER_A"].str.strip()
fights_clean["FIGHTER_B"] = fights_clean["FIGHTER_B"].str.strip()

print(
    fights_clean[
        ["BOUT", "FIGHTER_A", "FIGHTER_B", "OUTCOME"]
    ].head(10).to_string(index=False)
)

print("\nMissing Fighter A names:", fights_clean["FIGHTER_A"].isna().sum())
print("Missing Fighter B names:", fights_clean["FIGHTER_B"].isna().sum())

### Fight stats per round ###

fight_stats = pd.read_csv("data/ufc_fight_stats.csv")

print("\nFight-statistics shape:", fight_stats.shape)
print("Fight-statistics columns:")
print(fight_stats.columns.tolist())

print(fight_stats.head(5).to_string(index=False))

### Fighter TOTT ###

fighters = pd.read_csv("data/ufc_fighter_tott.csv")

print("\nFighter-data shape:", fighters.shape)
print("Fighter-data columns:")
print(fighters.columns.tolist())

print(fighters.head(10).to_string(index=False))

fighters_clean = fighters.copy()

fighters_clean["FIGHTER"] = fighters_clean["FIGHTER"].str.strip()

fighters_clean = fighters_clean.replace("--", pd.NA)

fighters_clean["DOB"] = pd.to_datetime(
    fighters_clean["DOB"],
    errors="coerce"
)

print("\nCleaned fighter data:")
print(fighters_clean.head(10).to_string(index=False))

print("\nMissing fighter values:")
print(fighters_clean.isna().sum())

fighters_clean["REACH_IN"] = pd.to_numeric(
    fighters_clean["REACH"].str.replace('"', "", regex=False),
    errors="coerce"
)

print(
    fighters_clean[
        ["FIGHTER", "REACH", "REACH_IN"]
    ].head(10).to_string(index=False)
)

print("\nREACH_IN data type:", fighters_clean["REACH_IN"].dtype)
print("Missing REACH_IN values:", fighters_clean["REACH_IN"].isna().sum())

def height_to_inches(height):
    if pd.isna(height):
        return None

    feet_text, inches_text = height.replace('"', "").split("'")

    feet = int(feet_text.strip())
    inches = int(inches_text.strip())

    return feet * 12 + inches


fighters_clean["HEIGHT_IN"] = fighters_clean["HEIGHT"].apply(
    height_to_inches
)

print(
    fighters_clean[
        ["FIGHTER", "HEIGHT", "HEIGHT_IN"]
    ].head(10).to_string(index=False)
)

print("\nHEIGHT_IN data type:", fighters_clean["HEIGHT_IN"].dtype)
print("Missing HEIGHT_IN values:", fighters_clean["HEIGHT_IN"].isna().sum())

fighters_clean["WEIGHT_LBS"] = pd.to_numeric(
    fighters_clean["WEIGHT"].str.replace(
        " lbs.",
        "",
        regex=False
    ),
    errors="coerce"
)

print(
    fighters_clean[
        ["FIGHTER", "WEIGHT", "WEIGHT_LBS"]
    ].head(10).to_string(index=False)
)

print("\nWEIGHT_LBS data type:", fighters_clean["WEIGHT_LBS"].dtype)
print("Missing WEIGHT_LBS values:", fighters_clean["WEIGHT_LBS"].isna().sum())

print("\nStance counts:")
print(
    fighters_clean["STANCE"].value_counts(
        dropna=False
    )
)

duplicate_profile_names = fighters_clean["FIGHTER"].duplicated().sum()

fight_fighter_names = set(
    fights_clean["FIGHTER_A"]
).union(
    fights_clean["FIGHTER_B"]
)

profile_fighter_names = set(
    fighters_clean["FIGHTER"]
)

missing_profile_names = sorted(
    fight_fighter_names - profile_fighter_names
)

print("\nDuplicate names in fighter profiles:", duplicate_profile_names)
print("Unique fighters appearing in fights:", len(fight_fighter_names))
print("Unique fighter profiles:", len(profile_fighter_names))
print("Fighters missing a profile:", len(missing_profile_names))

print("\nFirst missing profile names:")
print(missing_profile_names[:20])

duplicate_profiles = fighters_clean.loc[
    fighters_clean["FIGHTER"].duplicated(keep=False),
    [
        "FIGHTER",
        "HEIGHT",
        "WEIGHT",
        "REACH",
        "STANCE",
        "DOB",
        "URL"
    ]
].sort_values(["FIGHTER", "URL"])

print("\nProfiles with duplicated names:")
print(duplicate_profiles.to_string(index=False))

print(
    "\nNumber of duplicated-name groups:",
    duplicate_profiles["FIGHTER"].nunique()
)

duplicate_names = sorted(
    set(duplicate_profiles["FIGHTER"])
    .intersection(fight_fighter_names)
)

for name in duplicate_names:
    matching_fights = fights_clean.loc[
        (fights_clean["FIGHTER_A"] == name)
        | (fights_clean["FIGHTER_B"] == name),
        ["DATE", "BOUT", "WEIGHTCLASS"]
    ].sort_values("DATE")

    print(f"\nFights containing {name!r}:")
    print(matching_fights.to_string(index=False))

duplicate_fights = fights_clean.loc[
    fights_clean["URL"].duplicated(keep=False),
    [
        "DATE",
        "EVENT",
        "BOUT",
        "OUTCOME",
        "URL"
    ]
].sort_values(["URL", "EVENT"])

print(
    "\nNumber of repeated fight URLs:",
    fights_clean["URL"].duplicated().sum()
)

print(
    "Number of rows involved in repeated URLs:",
    len(duplicate_fights)
)

print("\nRepeated fight records:")
print(duplicate_fights.to_string(index=False))

repeated_url_count = fights_clean["URL"].duplicated().sum()
exact_duplicate_count = fights_clean.duplicated().sum()

print("\nRepeated fight URLs:", repeated_url_count)
print("Completely identical rows:", exact_duplicate_count)

assert repeated_url_count == exact_duplicate_count, (
    "Some repeated URLs contain conflicting data."
)

rows_before = len(fights_clean)

fights_clean = fights_clean.drop_duplicates(
    subset="URL",
    keep="first"
).copy()

rows_after = len(fights_clean)

print("\nRows before removing duplicates:", rows_before)
print("Rows after removing duplicates:", rows_after)
print("Rows removed:", rows_before - rows_after)
print(
    "Repeated URLs remaining:",
    fights_clean["URL"].duplicated().sum()
)

print("\nPossible matches for missing fighter profiles:")

for missing_name in missing_profile_names:
    possible_matches = get_close_matches(
        missing_name,
        sorted(profile_fighter_names),
        n=3,
        cutoff=0.55
    )

    print(f"{missing_name!r} -> {possible_matches}")

print("\nFights involving names with missing profiles:")

for missing_name in missing_profile_names:
    matching_fights = fights_clean.loc[
        (fights_clean["FIGHTER_A"] == missing_name)
        | (fights_clean["FIGHTER_B"] == missing_name),
        [
            "DATE",
            "EVENT",
            "BOUT",
            "WEIGHTCLASS"
        ]
    ].sort_values("DATE")

    print(f"\n{missing_name!r}:")
    print(matching_fights.to_string(index=False))

fighter_name_corrections = {
    "Cam Nelson": "Cameron Nelson",
    "Hector Santiago": "Hector de Sousa Santiago",
    "Kai Kamaka III": "Kai Kamaka",
    "Levi Rodrigues Jr.": "Levi Rodrigues",
    "Michael Aswell Jr.": "Michael Aswell",
    "Patricio Pitbull": "Patricio Freire",
    "Rafael Cerquiera": "Rafael Cerqueira",
    "Shem Rock": "Shaqueme Rock",
    "Waldo Cortes Acosta": "Waldo Cortes-Acosta",
    "YiSak Lee": "Yi Sak Lee",
    "Zach Reese": "Zachary Reese"
}

fights_clean["FIGHTER_A"] = fights_clean["FIGHTER_A"].replace(
    fighter_name_corrections
)

fights_clean["FIGHTER_B"] = fights_clean["FIGHTER_B"].replace(
    fighter_name_corrections
)

fight_fighter_names = set(
    fights_clean["FIGHTER_A"]
).union(
    fights_clean["FIGHTER_B"]
)

profile_fighter_names = set(
    fighters_clean["FIGHTER"]
)

missing_profile_names = sorted(
    fight_fighter_names - profile_fighter_names
)

print("\nFighters still missing profiles:", len(missing_profile_names))
print(missing_profile_names)

fighters_for_merge = fighters_clean.loc[
    fighters_clean["FIGHTER"].isin(fight_fighter_names)
].copy()

selected_profile_urls = {
    "Jean Silva":
        "http://ufcstats.com/fighter-details/52ef95b5860fb28c",

    "Joey Gomez":
        "http://ufcstats.com/fighter-details/0778f94eb5d588a5",

    "Michael McDonald":
        "http://ufcstats.com/fighter-details/d0314416a7f26527",

    "Mike Davis":
        "http://ufcstats.com/fighter-details/fb3e61720be4690c",

    "Victor Valenzuela":
        "http://ufcstats.com/fighter-details/078695e385ec2f57"
}

for fighter_name, selected_url in selected_profile_urls.items():
    fighters_for_merge = fighters_for_merge.loc[
        (fighters_for_merge["FIGHTER"] != fighter_name)
        | (fighters_for_merge["URL"] == selected_url)
    ].copy()

remaining_duplicate_profiles = fighters_for_merge.loc[
    fighters_for_merge["FIGHTER"].duplicated(keep=False),
    [
        "FIGHTER",
        "HEIGHT_IN",
        "WEIGHT_LBS",
        "REACH_IN",
        "DOB",
        "URL"
    ]
]

print("\nRemaining duplicated profiles:")
print(remaining_duplicate_profiles.to_string(index=False))

print(
    "\nRemaining duplicated-name groups:",
    remaining_duplicate_profiles["FIGHTER"].nunique()
)

fighters_for_merge["FIGHTER_KEY"] = fighters_for_merge["FIGHTER"]

flyweight_bruno_url = (
    "http://ufcstats.com/fighter-details/294aa73dbf37d281"
)

middleweight_bruno_url = (
    "http://ufcstats.com/fighter-details/12ebd7d157e91701"
)

fighters_for_merge.loc[
    fighters_for_merge["URL"] == flyweight_bruno_url,
    "FIGHTER_KEY"
] = "Bruno Silva [FLW]"

fighters_for_merge.loc[
    fighters_for_merge["URL"] == middleweight_bruno_url,
    "FIGHTER_KEY"
] = "Bruno Silva [MW]"

fights_clean["FIGHTER_A_KEY"] = fights_clean["FIGHTER_A"]
fights_clean["FIGHTER_B_KEY"] = fights_clean["FIGHTER_B"]

for fighter_column, key_column in [
    ("FIGHTER_A", "FIGHTER_A_KEY"),
    ("FIGHTER_B", "FIGHTER_B_KEY")
]:
    is_bruno = fights_clean[fighter_column].eq("Bruno Silva")

    is_middleweight = fights_clean["WEIGHTCLASS"].eq(
        "Middleweight Bout"
    )

    is_lower_weight_bruno = fights_clean["WEIGHTCLASS"].isin(
        ["Flyweight Bout", "Bantamweight Bout"]
    )

    fights_clean.loc[
        is_bruno & is_middleweight,
        key_column
    ] = "Bruno Silva [MW]"

    fights_clean.loc[
        is_bruno & is_lower_weight_bruno,
        key_column
    ] = "Bruno Silva [FLW]"


print(
    "\nDuplicate profile merge keys:",
    fighters_for_merge["FIGHTER_KEY"].duplicated().sum()
)

print(
    "Unresolved Fighter A Bruno keys:",
    (
        (fights_clean["FIGHTER_A"] == "Bruno Silva")
        & (fights_clean["FIGHTER_A_KEY"] == "Bruno Silva")
    ).sum()
)

print(
    "Unresolved Fighter B Bruno keys:",
    (
        (fights_clean["FIGHTER_B"] == "Bruno Silva")
        & (fights_clean["FIGHTER_B_KEY"] == "Bruno Silva")
    ).sum()
)

print(
    fighters_for_merge.loc[
        fighters_for_merge["FIGHTER"] == "Bruno Silva",
        ["FIGHTER", "FIGHTER_KEY", "WEIGHT_LBS", "DOB"]
    ].to_string(index=False)
)

fighter_a_profiles = fighters_for_merge[
    [
        "FIGHTER_KEY",
        "HEIGHT_IN",
        "REACH_IN",
        "STANCE",
        "DOB",
        "URL"
    ]
].rename(
    columns={
        "FIGHTER_KEY": "FIGHTER_A_KEY",
        "HEIGHT_IN": "A_HEIGHT_IN",
        "REACH_IN": "A_REACH_IN",
        "STANCE": "A_STANCE",
        "DOB": "A_DOB",
        "URL": "A_PROFILE_URL"
    }
)

fights_with_a_profile = fights_clean.merge(
    fighter_a_profiles,
    on="FIGHTER_A_KEY",
    how="left",
    validate="many_to_one"
)

print("\nRows before Fighter A merge:", len(fights_clean))
print("Rows after Fighter A merge:", len(fights_with_a_profile))

print(
    "Fighter A rows without a matching profile:",
    fights_with_a_profile["A_PROFILE_URL"].isna().sum()
)

print("\nUnmatched Fighter A names:")
print(
    fights_with_a_profile.loc[
        fights_with_a_profile["A_PROFILE_URL"].isna(),
        "FIGHTER_A"
    ].value_counts()
)

print(
    fights_with_a_profile[
        [
            "DATE",
            "FIGHTER_A",
            "A_HEIGHT_IN",
            "A_REACH_IN",
            "A_STANCE",
            "A_DOB"
        ]
    ].head(10).to_string(index=False)
)

fighter_b_profiles = fighters_for_merge[
    [
        "FIGHTER_KEY",
        "HEIGHT_IN",
        "REACH_IN",
        "STANCE",
        "DOB",
        "URL"
    ]
].rename(
    columns={
        "FIGHTER_KEY": "FIGHTER_B_KEY",
        "HEIGHT_IN": "B_HEIGHT_IN",
        "REACH_IN": "B_REACH_IN",
        "STANCE": "B_STANCE",
        "DOB": "B_DOB",
        "URL": "B_PROFILE_URL"
    }
)

fights_with_profiles = fights_with_a_profile.merge(
    fighter_b_profiles,
    on="FIGHTER_B_KEY",
    how="left",
    validate="many_to_one"
)

print("\nRows before Fighter B merge:", len(fights_with_a_profile))
print("Rows after Fighter B merge:", len(fights_with_profiles))

print(
    "Fighter B rows without a matching profile:",
    fights_with_profiles["B_PROFILE_URL"].isna().sum()
)

print("\nUnmatched Fighter B names:")
print(
    fights_with_profiles.loc[
        fights_with_profiles["B_PROFILE_URL"].isna(),
        "FIGHTER_B"
    ].value_counts()
)

print(
    fights_with_profiles[
        [
            "DATE",
            "FIGHTER_A",
            "A_HEIGHT_IN",
            "A_REACH_IN",
            "FIGHTER_B",
            "B_HEIGHT_IN",
            "B_REACH_IN"
        ]
    ].head(10).to_string(index=False)
)



########## Pre-fight features #############

### Age at time of fight ###

days_per_year = 365.2425

fights_with_profiles["A_AGE"] = (
    fights_with_profiles["DATE"]
    - fights_with_profiles["A_DOB"]
).dt.days / days_per_year

fights_with_profiles["B_AGE"] = (
    fights_with_profiles["DATE"]
    - fights_with_profiles["B_DOB"]
).dt.days / days_per_year


### Matchup differences ###

fights_with_profiles["AGE_DIFF"] = (
    fights_with_profiles["A_AGE"]
    - fights_with_profiles["B_AGE"]
)

fights_with_profiles["HEIGHT_DIFF"] = (
    fights_with_profiles["A_HEIGHT_IN"]
    - fights_with_profiles["B_HEIGHT_IN"]
)

fights_with_profiles["REACH_DIFF"] = (
    fights_with_profiles["A_REACH_IN"]
    - fights_with_profiles["B_REACH_IN"]
)

profile_feature_columns = [
    "AGE_DIFF",
    "HEIGHT_DIFF",
    "REACH_DIFF"
]

preview_columns = [
    "DATE",
    "FIGHTER_A",
    "A_AGE",
    "A_HEIGHT_IN",
    "A_REACH_IN",
    "FIGHTER_B",
    "B_AGE",
    "B_HEIGHT_IN",
    "B_REACH_IN",
    "AGE_DIFF",
    "HEIGHT_DIFF",
    "REACH_DIFF"
]

feature_preview = fights_with_profiles[
    preview_columns
].head(10).copy()

numeric_preview_columns = [
    "A_AGE",
    "A_HEIGHT_IN",
    "A_REACH_IN",
    "B_AGE",
    "B_HEIGHT_IN",
    "B_REACH_IN",
    "AGE_DIFF",
    "HEIGHT_DIFF",
    "REACH_DIFF"
]

feature_preview[numeric_preview_columns] = (
    feature_preview[numeric_preview_columns].round(2)
)

print("\nPre-fight profile feature preview:")
print(feature_preview.to_string(index=False))

print("\nPre-fight feature summary:")
print(
    fights_with_profiles[
        profile_feature_columns
    ].describe().round(2)
)

print("\nMissing pre-fight feature values:")
print(
    fights_with_profiles[
        profile_feature_columns
    ].isna().sum()
)

assert len(fights_with_profiles) == len(fights_clean)

assert fights_with_profiles["URL"].is_unique

assert fights_with_profiles["A_AGE"].dropna().between(15, 70).all()
assert fights_with_profiles["B_AGE"].dropna().between(15, 70).all()

difference_sources = {
    "AGE_DIFF": ("A_AGE", "B_AGE"),
    "HEIGHT_DIFF": ("A_HEIGHT_IN", "B_HEIGHT_IN"),
    "REACH_DIFF": ("A_REACH_IN", "B_REACH_IN")
}

for difference_column, source_columns in difference_sources.items():
    expected_missing = (
        fights_with_profiles[
            list(source_columns)
        ].isna().any(axis=1)
    )

    actual_missing = (
        fights_with_profiles[difference_column].isna()
    )

    assert actual_missing.equals(expected_missing)

for column in profile_feature_columns:
    assert pd.api.types.is_numeric_dtype(
        fights_with_profiles[column]
    )

postfight_columns = {
    "OUTCOME",
    "METHOD",
    "ROUND",
    "TIME",
    "DETAILS"
}

assert postfight_columns.isdisjoint(
    profile_feature_columns
)

print("\nAll profile-feature validation checks passed.")



fighter_a_appearances = fights_with_profiles[
    [
        "URL",
        "DATE",
        "BOUT",
        "OUTCOME",
        "FIGHTER_A",
        "FIGHTER_A_KEY"
    ]
].copy()

fighter_a_appearances = fighter_a_appearances.rename(
    columns={
        "URL": "FIGHT_URL",
        "FIGHTER_A": "FIGHTER",
        "FIGHTER_A_KEY": "FIGHTER_KEY"
    }
)

fighter_a_appearances["SIDE"] = "A"

fighter_a_appearances["WIN"] = (
    fighter_a_appearances["OUTCOME"] == "W/L"
).astype(int)

fighter_a_appearances["DECISIVE"] = (
    fighter_a_appearances["OUTCOME"].isin(["W/L", "L/W"])
).astype(int)

fighter_b_appearances = fights_with_profiles[
    [
        "URL",
        "DATE",
        "BOUT",
        "OUTCOME",
        "FIGHTER_B",
        "FIGHTER_B_KEY"
    ]
].copy()

fighter_b_appearances = fighter_b_appearances.rename(
    columns={
        "URL": "FIGHT_URL",
        "FIGHTER_B": "FIGHTER",
        "FIGHTER_B_KEY": "FIGHTER_KEY"
    }
)

fighter_b_appearances["SIDE"] = "B"

fighter_b_appearances["WIN"] = (
    fighter_b_appearances["OUTCOME"] == "L/W"
).astype(int)

fighter_b_appearances["DECISIVE"] = (
    fighter_b_appearances["OUTCOME"].isin(["W/L", "L/W"])
).astype(int)

fighter_appearances = pd.concat(
    [
        fighter_a_appearances,
        fighter_b_appearances
    ],
    ignore_index=True
)

assert len(fighter_appearances) == 2 * len(fights_with_profiles)

assert (
    fighter_appearances["FIGHT_URL"]
    .value_counts()
    .eq(2)
    .all()
)


########## Create one historical update per fighter/date #############

fighter_daily_history = (
    fighter_appearances
    .groupby(
        ["FIGHTER_KEY", "DATE"],
        as_index=False
    )
    .agg(
        DECISIVE_FIGHTS_TODAY=("DECISIVE", "sum"),
        WINS_TODAY=("WIN", "sum")
    )
    .sort_values(["FIGHTER_KEY", "DATE"])
    .reset_index(drop=True)
)


### Calculate record BEFORE the current date ###

fighter_daily_history["PRIOR_UFC_FIGHTS"] = (
    fighter_daily_history
    .groupby("FIGHTER_KEY")["DECISIVE_FIGHTS_TODAY"]
    .cumsum()
    - fighter_daily_history["DECISIVE_FIGHTS_TODAY"]
)

fighter_daily_history["PRIOR_UFC_WINS"] = (
    fighter_daily_history
    .groupby("FIGHTER_KEY")["WINS_TODAY"]
    .cumsum()
    - fighter_daily_history["WINS_TODAY"]
)

fighter_daily_history["PRIOR_UFC_LOSSES"] = (
    fighter_daily_history["PRIOR_UFC_FIGHTS"]
    - fighter_daily_history["PRIOR_UFC_WINS"]
)

fighter_daily_history["PRIOR_UFC_WIN_RATE"] = (
    fighter_daily_history["PRIOR_UFC_WINS"]
    / fighter_daily_history["PRIOR_UFC_FIGHTS"]
).where(
    fighter_daily_history["PRIOR_UFC_FIGHTS"] > 0
)


### Days since previous UFC appearance ###

fighter_daily_history["PREVIOUS_UFC_FIGHT_DATE"] = (
    fighter_daily_history
    .groupby("FIGHTER_KEY")["DATE"]
    .shift(1)
)

fighter_daily_history["DAYS_SINCE_LAST_FIGHT"] = (
    fighter_daily_history["DATE"]
    - fighter_daily_history["PREVIOUS_UFC_FIGHT_DATE"]
).dt.days


########## Validate chronological calculations #############

first_fighter_dates = (
    fighter_daily_history
    .groupby("FIGHTER_KEY")
    .head(1)
)

assert first_fighter_dates["PRIOR_UFC_FIGHTS"].eq(0).all()
assert first_fighter_dates["PRIOR_UFC_WINS"].eq(0).all()
assert first_fighter_dates["PREVIOUS_UFC_FIGHT_DATE"].isna().all()

assert (
    fighter_daily_history["PRIOR_UFC_WINS"]
    <= fighter_daily_history["PRIOR_UFC_FIGHTS"]
).all()

assert (
    fighter_daily_history["DAYS_SINCE_LAST_FIGHT"]
    .dropna()
    .gt(0)
    .all()
)

assert (
    fighter_daily_history["PRIOR_UFC_WIN_RATE"]
    .dropna()
    .between(0, 1)
    .all()
)

history_columns = [
    "PRIOR_UFC_FIGHTS",
    "PRIOR_UFC_WINS",
    "PRIOR_UFC_LOSSES",
    "PRIOR_UFC_WIN_RATE",
    "PREVIOUS_UFC_FIGHT_DATE",
    "DAYS_SINCE_LAST_FIGHT"
]

fighter_appearances_with_history = fighter_appearances.merge(
    fighter_daily_history[
        [
            "FIGHTER_KEY",
            "DATE",
            *history_columns
        ]
    ],
    on=["FIGHTER_KEY", "DATE"],
    how="left",
    validate="many_to_one"
)


########## Separate Fighter A history #############

fighter_a_history = fighter_appearances_with_history.loc[
    fighter_appearances_with_history["SIDE"] == "A",
    [
        "FIGHT_URL",
        *history_columns
    ]
].copy()

fighter_a_history = fighter_a_history.rename(
    columns={"FIGHT_URL": "URL"}
)

fighter_a_history = fighter_a_history.rename(
    columns={
        column: f"A_{column}"
        for column in history_columns
    }
)


########## Separate Fighter B history #############

fighter_b_history = fighter_appearances_with_history.loc[
    fighter_appearances_with_history["SIDE"] == "B",
    [
        "FIGHT_URL",
        *history_columns
    ]
].copy()

fighter_b_history = fighter_b_history.rename(
    columns={"FIGHT_URL": "URL"}
)

fighter_b_history = fighter_b_history.rename(
    columns={
        column: f"B_{column}"
        for column in history_columns
    }
)

assert fighter_a_history["URL"].is_unique
assert fighter_b_history["URL"].is_unique


########## Merge both histories into the fight table #############

fights_with_history = fights_with_profiles.merge(
    fighter_a_history,
    on="URL",
    how="left",
    validate="one_to_one"
)

fights_with_history = fights_with_history.merge(
    fighter_b_history,
    on="URL",
    how="left",
    validate="one_to_one"
)

assert len(fights_with_history) == len(fights_with_profiles)
assert fights_with_history["URL"].is_unique


########## Historical matchup differences #############

fights_with_history["PRIOR_FIGHTS_DIFF"] = (
    fights_with_history["A_PRIOR_UFC_FIGHTS"]
    - fights_with_history["B_PRIOR_UFC_FIGHTS"]
)

fights_with_history["PRIOR_WIN_RATE_DIFF"] = (
    fights_with_history["A_PRIOR_UFC_WIN_RATE"]
    - fights_with_history["B_PRIOR_UFC_WIN_RATE"]
)

fights_with_history["DAYS_SINCE_LAST_FIGHT_DIFF"] = (
    fights_with_history["A_DAYS_SINCE_LAST_FIGHT"]
    - fights_with_history["B_DAYS_SINCE_LAST_FIGHT"]
)


########## Remove draws/NCs and create target #############

phase1_rows = fights_with_history.loc[
    fights_with_history["OUTCOME"].isin(["W/L", "L/W"])
].copy()

phase1_rows["TARGET"] = phase1_rows["OUTCOME"].map(
    {
        "W/L": 1,
        "L/W": 0
    }
).astype(int)

phase1_rows = phase1_rows.sort_values(
    ["DATE", "URL"]
).reset_index(drop=True)


########## Phase 1 model features #############

phase1_feature_columns = [
    "AGE_DIFF",
    "HEIGHT_DIFF",
    "REACH_DIFF",
    "PRIOR_FIGHTS_DIFF",
    "PRIOR_WIN_RATE_DIFF",
    "DAYS_SINCE_LAST_FIGHT_DIFF"
]

phase1_output_columns = [
    "URL",
    "DATE",
    "EVENT",
    "BOUT",
    "WEIGHTCLASS",
    "FIGHTER_A",
    "FIGHTER_B",
    "FIGHTER_A_KEY",
    "FIGHTER_B_KEY",

    "TARGET",

    "A_AGE",
    "B_AGE",
    "A_HEIGHT_IN",
    "B_HEIGHT_IN",
    "A_REACH_IN",
    "B_REACH_IN",

    "A_PRIOR_UFC_FIGHTS",
    "B_PRIOR_UFC_FIGHTS",
    "A_PRIOR_UFC_WINS",
    "B_PRIOR_UFC_WINS",
    "A_PRIOR_UFC_LOSSES",
    "B_PRIOR_UFC_LOSSES",
    "A_PRIOR_UFC_WIN_RATE",
    "B_PRIOR_UFC_WIN_RATE",
    "A_PREVIOUS_UFC_FIGHT_DATE",
    "B_PREVIOUS_UFC_FIGHT_DATE",
    "A_DAYS_SINCE_LAST_FIGHT",
    "B_DAYS_SINCE_LAST_FIGHT",

    *phase1_feature_columns
]

phase1_model_data = phase1_rows[
    phase1_output_columns
].copy()


########## Final validation #############

assert phase1_model_data["URL"].is_unique
assert phase1_model_data["TARGET"].isin([0, 1]).all()
assert phase1_model_data["DATE"].is_monotonic_increasing

assert (
    phase1_model_data["A_PRIOR_UFC_WINS"]
    + phase1_model_data["A_PRIOR_UFC_LOSSES"]
    == phase1_model_data["A_PRIOR_UFC_FIGHTS"]
).all()

assert (
    phase1_model_data["B_PRIOR_UFC_WINS"]
    + phase1_model_data["B_PRIOR_UFC_LOSSES"]
    == phase1_model_data["B_PRIOR_UFC_FIGHTS"]
).all()

for feature in phase1_feature_columns:
    assert pd.api.types.is_numeric_dtype(
        phase1_model_data[feature]
    )

forbidden_columns = {
    "OUTCOME",
    "METHOD",
    "ROUND",
    "TIME",
    "DETAILS"
}

assert forbidden_columns.isdisjoint(
    phase1_model_data.columns
)

from pathlib import Path

output_path = Path(
    "data/processed/phase1_model_data.csv"
)

output_path.parent.mkdir(
    parents=True,
    exist_ok=True
)

phase1_model_data.to_csv(
    output_path,
    index=False
)

print("\nPhase 1 modeling-data shape:", phase1_model_data.shape)

print("\nTarget counts:")
print(
    phase1_model_data["TARGET"]
    .value_counts()
    .sort_index()
)

print("\nMissing model-feature values:")
print(
    phase1_model_data[
        phase1_feature_columns
    ].isna().sum()
)

print("\nDate range:")
print(
    phase1_model_data["DATE"].min(),
    "through",
    phase1_model_data["DATE"].max()
)

print("\nSaved modeling data to:", output_path)
print("\nAll Phase 1 data checks passed.")