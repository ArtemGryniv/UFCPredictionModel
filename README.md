# UFC Fight Outcome Prediction

An ongoing machine-learning project that predicts the probability of Fighter A defeating Fighter B using only information available before the fight.

## Phase 1

Phase 1 uses logistic regression with six matchup-difference features:

- Age
- Height
- Reach
- Previous UFC fights
- Previous UFC win rate
- Days since last UFC fight

Historical features are calculated chronologically before adding the current fight's result, preventing future-data leakage. Draws and no-contests are excluded from the target.

## Results

- Trained on 6,959 older fights and tested on 1,746 newer fights
- Achieved 59.14% accuracy compared with a 50% neutral baseline
- Improved log loss from 0.6931 to 0.6628
- Improved Brier score from 0.2500 to 0.2353
- Produced symmetric probabilities when fighter order was reversed
- Showed generally good calibration, although extreme predictions were somewhat conservative

## Data

Data comes from UFCStats CSV files collected by the [Greco1899 scrape_ufc_stats project](https://github.com/Greco1899/scrape_ufc_stats).

Required files:

- `ufc_fight_results.csv`
- `ufc_event_details.csv`
- `ufc_fight_stats.csv`
- `ufc_fighter_tott.csv`

CSV files and generated datasets are excluded from Git.

## Phase 2 Plan

- Perform detailed error analysis
- Add leakage-safe historical striking, takedown, and control statistics
- Explore recency-weighted performance and opponent strength
- Compare logistic regression with tree-based models
- Improve probability calibration
- Build a reusable pipeline for predicting new matchups

