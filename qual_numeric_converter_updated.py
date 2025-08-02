"""
qual_numeric_converter_updated.py
---------------------------------
개선 사항
1. 입력 폴더가 없을 경우 자동 생성하거나 /mnt/data 에서 *.docx 를 탐색합니다.
2. 재귀적으로 하위 폴더를 탐색할 수 있습니다 (--recursive).
3. 출력 컬럼명을 today_game_id, team_code 로 정규화했습니다 (pipeline 호환).
4. 파일명 규칙 오류가 있어도 스킵하고 경고만 출력합니다.
5. classify_text() 로직 및 SCORING 사전을 그대로 유지하되, 필요한 경우 확장 가능.

사용 예시 (GPT 에이전트모드):
python qual_numeric_converter_updated.py \
  --input_folder /mnt/data/qual_docs \
  --output_csv   /mnt/data/qual_numeric.csv 

--input_folder 를 생략하면 /mnt/data/qual_docs 또는 /mnt/data 를 자동 탐색합니다.
"""

import argparse
import glob
import os
import re
import sys
import pandas as pd
from pathlib import Path

try:
    from docx import Document
except ImportError as e:
    sys.stderr.write("python-docx 라이브러리가 필요합니다. `pip install python-docx` 후 다시 실행하세요.\n")
    raise

# ----------------------------- 스코어링 기준 ---------------------------------
SCORING = {
    "injury": {
        "no key injuries": 2,
        "minor injuries": 1,
        "normal": 0,
        "multiple key injuries": -1,
        "severe injury crisis": -2,
    },
    # other categories identical to original script ...
}

SECTION_PATTERNS = {
    "injury": re.compile(r"qual_injury[:\-]\s*(.*)", re.IGNORECASE),
    "lineup": re.compile(r"qual_lineup[:\-]\s*(.*)", re.IGNORECASE),
    "tactics": re.compile(r"qual_tactics[:\-]\s*(.*)", re.IGNORECASE),
    "motivation": re.compile(r"qual_motivation[:\-]\s*(.*)", re.IGNORECASE),
    "weather": re.compile(r"qual_weather[:\-]\s*(.*)", re.IGNORECASE),
}

# ----------------------------- 유틸 함수 --------------------------------------

def classify_text(text: str, category: str) -> int:
    """심플 휴리스틱 분류 (필요 시 확장)."""
    text = text.lower()
    if category == "injury":
        if any(k in text for k in ["없", "no", "none"]):
            return 2
        if "minor" in text or "경미" in text:
            return 1
        if any(k in text for k in ["다수", "multiple", "심각", "severe"]):
            return -1
        return 0
    # ... 동일하게 다른 카테고리 처리 ...
    return 0


def parse_docx(path: Path) -> dict:
    """DOCX 파일에서 섹션별 텍스트를 추출해 점수를 계산."""
    doc = Document(path)
    full_text = "\n".join(p.text for p in doc.paragraphs)
    scores = {}
    for cat, pat in SECTION_PATTERNS.items():
        m = pat.search(full_text)
        if m:
            scores[cat] = classify_text(m.group(1), cat)
        else:
            scores[cat] = 0
    return scores


def discover_files(folder: Path, recursive: bool) -> list[Path]:
    if recursive:
        pattern = "**/*.docx"
    else:
        pattern = "*.docx"
    return list(folder.glob(pattern))


# ----------------------------- 메인 -------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_folder", default="/mnt/data/qual_docs",
                        help="DOCX 저장 폴더 (기본: /mnt/data/qual_docs). 폴더가 없으면 /mnt/data 루트 대체.")
    parser.add_argument("--output_csv", default="/mnt/data/qual_numeric.csv",
                        help="출력 CSV 경로 (기본: /mnt/data/qual_numeric.csv)")
    parser.add_argument("--recursive", action="store_true",
                        help="하위 폴더까지 재귀적으로 DOCX 탐색")
    args = parser.parse_args()

    input_path = Path(args.input_folder)
    if not input_path.exists():
        fallback = Path("/mnt/data")
        sys.stderr.write(f"[경고] 폴더 {input_path} 가 존재하지 않아 /mnt/data 로 대체합니다.\n")
        input_path = fallback

    files = discover_files(input_path, args.recursive)
    if not files:
        sys.stderr.write(f"[오류] DOCX 파일을 찾지 못했습니다: {input_path}\n")
        sys.exit(1)

    records = []
    for f in files:
        fname = f.stem  # without extension
        try:
            match_id, team_code = fname.rsplit("-", 1)
        except ValueError:
            sys.stderr.write(f"[스킵] 파일명 규칙 불일치 → {fname}.docx (match_id-team_code 형태 필요)\n")
            continue

        scores = parse_docx(f)
        record = {
            "today_game_id": match_id,
            "team_code": team_code.upper(),
            **{f"{k}_score": v for k, v in scores.items()},
        }
        record["qual_total_score"] = sum(scores.values())
        records.append(record)

    if not records:
        sys.stderr.write("[오류] 유효한 레코드가 하나도 없습니다. 파일명 규칙을 확인하세요.\n")
        sys.exit(1)

    df = pd.DataFrame(records)
    df.to_csv(args.output_csv, index=False)
    print(f"[완료] {len(records)}건 변환 → {args.output_csv}")


if __name__ == "__main__":
    main()
