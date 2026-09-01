from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from sklearn.metrics import (
    accuracy_score,
    log_loss,
    brier_score_loss
)


# Load data

data_path = Path(
    "data/processed/phase1_model_data.csv"
)

data = pd.read_csv(
    data_path,
    parse_dates=["DATE"]
)

data = data.sort_values(
    ["DATE", "URL"]
).reset_index(drop=True)


feature_columns = [
    "AGE_DIFF",
    "HEIGHT_DIFF",
    "REACH_DIFF",
    "PRIOR_FIGHTS_DIFF",
    "PRIOR_WIN_RATE_DIFF",
    "DAYS_SINCE_LAST_FIGHT_DIFF"
]


# Chronologically split train/test data

split_position = int(len(data) * 0.80)
cutoff_date = data.iloc[split_position]["DATE"]

train_data = data.loc[
    data["DATE"] < cutoff_date
].copy()

test_data = data.loc[
    data["DATE"] >= cutoff_date
].copy()

assert len(train_data) > 0
assert len(test_data) > 0
assert train_data["DATE"].max() < test_data["DATE"].min()

print("Cutoff date:", cutoff_date.date())
print("Training fights:", len(train_data))
print("Test fights:", len(test_data))
print("Latest training date:", train_data["DATE"].max().date())
print("Earliest test date:", test_data["DATE"].min().date())

X_train = train_data[feature_columns].reset_index(drop=True)
y_train = train_data["TARGET"].reset_index(drop=True)

X_test = test_data[feature_columns].reset_index(drop=True)
y_test = test_data["TARGET"].reset_index(drop=True)



########## Add mirrored training rows #############

# Every feature is Fighter A minus Fighter B.
# Swapping the fighters therefore changes every feature's sign.

X_train_mirrored = -X_train
y_train_mirrored = 1 - y_train

X_train_augmented = pd.concat(
    [X_train, X_train_mirrored],
    ignore_index=True
)

y_train_augmented = pd.concat(
    [y_train, y_train_mirrored],
    ignore_index=True
)

assert y_train_augmented.mean() == 0.5

print("\nOriginal training rows:", len(X_train))
print("Training rows after mirroring:", len(X_train_augmented))


# Logistic Regression Pipeline

model = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="median")
        ),
        (
            "scaler",
            StandardScaler()
        ),
        (
            "classifier",
            LogisticRegression(
                max_iter=2000,
                random_state=42
            )
        )
    ]
)


# Train model
model.fit(
    X_train_augmented,
    y_train_augmented
)


########## Create order-neutral test evaluation #############

# Evaluate every test fight in both orientations.
# This produces a perfectly balanced evaluation set.

X_test_mirrored = -X_test
y_test_mirrored = 1 - y_test

X_test_evaluation = pd.concat(
    [X_test, X_test_mirrored],
    ignore_index=True
)

y_test_evaluation = pd.concat(
    [y_test, y_test_mirrored],
    ignore_index=True
)


# Make predictions

predicted_probabilities = model.predict_proba(
    X_test_evaluation
)[:, 1]

predicted_classes = (
    predicted_probabilities >= 0.50
).astype(int)

# Evaluate

model_accuracy = accuracy_score(
    y_test_evaluation,
    predicted_classes
)

model_log_loss = log_loss(
    y_test_evaluation,
    predicted_probabilities
)

model_brier_score = brier_score_loss(
    y_test_evaluation,
    predicted_probabilities
)


# Neutral probability baseline

baseline_probabilities = np.full(
    len(y_test_evaluation),
    0.50
)

baseline_classes = (
    baseline_probabilities > 0.50
).astype(int)

baseline_accuracy = accuracy_score(
    y_test_evaluation,
    baseline_classes
)

baseline_log_loss = log_loss(
    y_test_evaluation,
    baseline_probabilities
)

baseline_brier_score = brier_score_loss(
    y_test_evaluation,
    baseline_probabilities
)


# Win-rate heuristic baseline 

win_rate_difference = (
    X_test_evaluation["PRIOR_WIN_RATE_DIFF"]
    .fillna(0)
)

win_rate_predictions = (
    win_rate_difference > 0
).astype(int)

win_rate_accuracy = accuracy_score(
    y_test_evaluation,
    win_rate_predictions
)


########## Display results #############

print("\nNeutral 50% baseline:")
print("Accuracy:", round(baseline_accuracy, 4))
print("Log loss:", round(baseline_log_loss, 4))
print("Brier score:", round(baseline_brier_score, 4))

print("\nPrior-win-rate heuristic:")
print("Accuracy:", round(win_rate_accuracy, 4))

print("\nLogistic regression:")
print("Accuracy:", round(model_accuracy, 4))
print("Log loss:", round(model_log_loss, 4))
print("Brier score:", round(model_brier_score, 4))


########## Inspect coefficients #############

coefficients = pd.Series(
    model.named_steps["classifier"].coef_[0],
    index=feature_columns
).sort_values(ascending=False)

print("\nStandardized logistic-regression coefficients:")
print(coefficients)




### Probabilistic win-rate-only baseline ###

win_rate_only_model = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="median")
        ),
        (
            "scaler",
            StandardScaler()
        ),
        (
            "classifier",
            LogisticRegression(
                max_iter=2000,
                random_state=42
            )
        )
    ]
)

win_rate_only_model.fit(
    X_train_augmented[["PRIOR_WIN_RATE_DIFF"]],
    y_train_augmented
)

win_rate_only_probabilities = (
    win_rate_only_model.predict_proba(
        X_test_evaluation[["PRIOR_WIN_RATE_DIFF"]]
    )[:, 1]
)

win_rate_only_predictions = (
    win_rate_only_probabilities >= 0.50
).astype(int)

print("\nWin-rate-only logistic regression:")
print(
    "Accuracy:",
    round(
        accuracy_score(
            y_test_evaluation,
            win_rate_only_predictions
        ),
        4
    )
)

print(
    "Log loss:",
    round(
        log_loss(
            y_test_evaluation,
            win_rate_only_probabilities
        ),
        4
    )
)

print(
    "Brier score:",
    round(
        brier_score_loss(
            y_test_evaluation,
            win_rate_only_probabilities
        ),
        4
    )
)

forward_probabilities = model.predict_proba(
    X_test
)[:, 1]

reverse_probabilities = model.predict_proba(
    -X_test
)[:, 1]

symmetric_probabilities = (
    forward_probabilities
    + (1 - reverse_probabilities)
) / 2

symmetry_error = np.abs(
    forward_probabilities
    - (1 - reverse_probabilities)
).max()

print(
    "\nMaximum A/B symmetry error:",
    symmetry_error
)


# Calibration table 

calibration_data = pd.DataFrame(
    {
        "PREDICTED_PROBABILITY": predicted_probabilities,
        "ACTUAL_RESULT": y_test_evaluation
    }
)

calibration_data["PROBABILITY_BIN"] = pd.qcut(
    calibration_data["PREDICTED_PROBABILITY"],
    q=10,
    duplicates="drop"
)

calibration_table = (
    calibration_data
    .groupby(
        "PROBABILITY_BIN",
        observed=True
    )
    .agg(
        FIGHTS=("ACTUAL_RESULT", "size"),
        AVERAGE_PREDICTION=(
            "PREDICTED_PROBABILITY",
            "mean"
        ),
        ACTUAL_WIN_RATE=(
            "ACTUAL_RESULT",
            "mean"
        )
    )
)

calibration_table["CALIBRATION_GAP"] = (
    calibration_table["ACTUAL_WIN_RATE"]
    - calibration_table["AVERAGE_PREDICTION"]
)

print("\nCalibration table:")
print(calibration_table.round(3).to_string())