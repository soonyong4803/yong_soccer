
#!/usr/bin/env python3
"""
train_models.py
----------------
* Train LightGBM multiclass models for multiple leagues
* Save model pickles + calibrated prediction XLSX per league
* Minimal feature engineering: use numeric columns (prefix 'feat_') + qualitative cols (qual_*)
Assumes feature files <league>_matches_YYYYMMDD.xlsx exist under /mnt/data
Label column: 'result' (0=H,1=D,2=A)
"""

import argparse, pathlib, datetime as dt, pandas as pd, numpy as np, joblib, glob, re, os, lightgbm as lgb

def latest_feature_file(league: str) -> pathlib.Path:
    files = sorted(glob.glob(f"/mnt/data/{league.lower()}_matches_*.xlsx"))
    if not files:
        raise FileNotFoundError(f"No feature files for {league}")
    return pathlib.Path(files[-1])

def prepare_data(df: pd.DataFrame):
    # select numeric cols
    feature_cols = [c for c in df.columns if c.startswith("feat_") or c.startswith("qual_") or c.endswith("_score") or c in ["rest_days","travel_km"]]
    X = df[feature_cols].fillna(0)
    y = df["result"]
    return X, y, feature_cols

def train_lgbm(X, y):
    params = dict(objective="multiclass", num_class=3, learning_rate=0.05, n_estimators=300,
                  max_depth=-1, subsample=0.8, colsample_bytree=0.8)
    model = lgb.LGBMClassifier(**params)
    model.fit(X, y)
    return model

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD (matches before this date used for training)")
    ap.add_argument("--leagues", nargs="+", required=True, help="e.g. J2 K1 K2")
    ap.add_argument("--model-dir", default="/mnt/data/models")
    ap.add_argument("--output-dir", default="/mnt/data")
    args = ap.parse_args()

    train_cutoff = dt.datetime.strptime(args.date, "%Y-%m-%d").date()
    pathlib.Path(args.model_dir).mkdir(parents=True, exist_ok=True)

    for lg in args.leagues:
        feat_path = latest_feature_file(lg)
        df = pd.read_excel(feat_path)

        df_train = df[df["date"].dt.date < train_cutoff]
        if "result" not in df_train.columns:
            raise ValueError(f"{feat_path} must contain 'result' column")

        X, y, feat_cols = prepare_data(df_train)
        model = train_lgbm(X, y)
        joblib.dump({"model": model, "features": feat_cols}, f"{args.model_dir}/{lg.lower()}_lgbm.pkl")

        # Generate calibrated preds for all rows (including pre‑match for reference)
        preds = model.predict_proba(df[feat_cols].fillna(0))
        df_out = df[["today_game_id","home_team","away_team"]].copy()
        df_out[["P_H","P_D","P_A"]] = preds
        df_out.to_excel(f"{args.output_dir}/{lg.lower()}_predictions_calibrated.xlsx", index=False)

        print(f"[{lg}] model saved & predictions exported")

if __name__ == "__main__":
    main()
