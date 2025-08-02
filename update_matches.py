
#!/usr/bin/env python3
"""update_matches.py
---------------------------------
Fetch latest match data for a single league and convert to feature file
compatible with the 용축구확률 pipeline.

Basic steps
-----------
1. Download fixtures + results for the given league from FootyStats API
   (requires env FOOTYSTATS_KEY or --api-key).
2. Engineer essential numeric features (date, home/away team, result, etc.).
3. Merge qualitative CSV (score columns) if provided.
4. Optionally merge with an existing feature file (keeps unique today_game_id).
5. Save as <league>_matches_YYYYMMDD.xlsx under --output-dir.

NOTE:
• This is a minimal working example; extend feature engineering as needed.
• FootyStats free tier limits requests — consider local caching if rate‑limited.
"""

import argparse, datetime as dt, os, pathlib, requests, pandas as pd, sys, json

API_BASE = "https://api.footystats.org/league-matches"

def fetch_matches(league_id: int, from_date: str, to_date: str, api_key: str) -> list[dict]:
    """Call FootyStats API and return list of match dicts."""
    params = {
        "key": api_key,
        "league_id": league_id,
        "from": from_date,
        "to": to_date
    }
    print(f"[FootyStats] GET {API_BASE} for {from_date}‑{to_date}")
    r = requests.get(API_BASE, params=params, timeout=60)
    r.raise_for_status()
    return r.json().get("data", [])

def make_today_game_id(row) -> str:
    date_part = row["date"].strftime("%Y%m%d")
    home_code = row["home_team"][:3].upper()
    away_code = row["away_team"][:3].upper()
    return f"{date_part}-{home_code}-{away_code}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", required=True, help="League code e.g. J2")
    ap.add_argument("--league-id", required=True, type=int, help="FootyStats league_id")
    ap.add_argument("--merge-qual", default="", help="qual_numeric CSV to merge")
    ap.add_argument("--merge-existing", default="", help="existing feature xlsx to merge/append")
    ap.add_argument("--output-dir", default="/mnt/data", help="directory to save output xlsx")
    ap.add_argument("--api-key", default=os.getenv("FOOTYSTATS_KEY", ""), help="FootyStats API Key")
    args = ap.parse_args()

    if not args.api_key:
        sys.exit("ERROR: Provide FootyStats API key via --api-key or FOOTYSTATS_KEY env")

    today = dt.date.today()
    from_date = (today - dt.timedelta(days=365)).strftime("%Y-%m-%d")  # 1y history
    to_date = today.strftime("%Y-%m-%d")

    # Fetch raw JSON
    matches = fetch_matches(args.league_id, from_date, to_date, args.api_key)
    if not matches:
        sys.exit("No matches returned from API; check league_id/date range")

    # Basic → DataFrame
    records = []
    for m in matches:
        rec = {
            "date": pd.to_datetime(m["match_date"]),
            "home_team": m["home_name"],
            "away_team": m["away_name"],
            "home_score": m["homeGoalCount"],
            "away_score": m["awayGoalCount"],
            "result": 0 if m["homeGoalCount"] > m["awayGoalCount"] else 2 if m["homeGoalCount"] < m["awayGoalCount"] else 1,
            # stub feature examples
            "feat_home_xg": m.get("home_xg", None),
            "feat_away_xg": m.get("away_xg", None),
        }
        records.append(rec)
    df = pd.DataFrame(records)
    df["today_game_id"] = df.apply(make_today_game_id, axis=1)
    df["team_code"] = df["home_team"].str[:3].str.upper()  # for merge with qual

    # Merge qualitative scores
    if args.merge_qual and pathlib.Path(args.merge_qual).exists():
        qual = pd.read_csv(args.merge_qual)
        df = df.merge(qual, on=["today_game_id", "team_code"], how="left")

    # Merge existing (keep newest)
    if args.merge_existing and pathlib.Path(args.merge_existing).exists():
        old = pd.read_excel(args.merge_existing)
        df = pd.concat([old, df], ignore_index=True).drop_duplicates("today_game_id", keep="last")

    # Save
    out_path = pathlib.Path(args.output_dir) / f"{args.league.lower()}_matches_{today.strftime('%Y%m%d')}.xlsx"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(out_path, index=False)
    print(f"✅ Saved → {out_path}")

if __name__ == "__main__":
    main()
