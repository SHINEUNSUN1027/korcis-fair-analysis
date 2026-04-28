"""
02_field_analysis.py
KORMARC 태그별 출현 빈도 및 기관별 메타데이터 품질 분석

입력: data/processed/parsed_records.csv
출력:
  - results/table3_field_frequency.csv  (논문 표 3)
  - results/table4_institution.csv      (논문 표 4)
  - data/processed/field_frequency.csv
  - data/processed/institution_quality.csv
"""

import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# 분석 대상 태그 및 한국어 명칭
TAG_LABELS = {
    "245": "서명저자사항",
    "300": "형태사항",
    "260": "간사사항",
    "250": "판사항",
    "100": "기본표목-개인명",
    "700": "부출표목-개인명",
    "653": "비통제 색인어",
    "650": "일반주제명",
    "600": "주제명부출-개인명",
    "651": "지명주제",
    "856": "전자적 위치 및 접속",
}

# KORMARC 필드 유형 (M=필수, MA=해당시필수, O=재량)
FIELD_TYPES = {
    "245": "M",
    "300": "M",
    "260": "M",
    "250": "MA",
    "100": "O",
    "700": "O",
    "653": "O",
    "650": "O",
    "600": "O",
    "651": "O",
    "856": "MA",
}

# 상위 N개 기관 분석
TOP_N_INSTITUTIONS = 10


def load_data():
    path = PROCESSED_DIR / "parsed_records.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} 없음. 01_parse_kormarc.py를 먼저 실행하세요.")
    df = pd.read_csv(path, low_memory=False)
    print(f"로드: {len(df):,}건, {df['library_code'].nunique()}개 기관")
    return df


def analyze_field_frequency(df: pd.DataFrame) -> pd.DataFrame:
    """태그별 출현 빈도 분석 — 논문 표 3"""
    total = len(df)
    rows = []
    for tag, label in TAG_LABELS.items():
        col = f"has_{tag}"
        if col not in df.columns:
            continue
        count = df[col].sum()
        rate = count / total * 100
        rows.append({
            "태그": tag,
            "필드명": label,
            "필드유형": FIELD_TYPES.get(tag, "O"),
            "출현건수": int(count),
            "출현율(%)": round(rate, 2),
            "비고": _get_note(tag),
        })
    result = pd.DataFrame(rows)
    result = result.sort_values("출현건수", ascending=False)
    return result


def _get_note(tag: str) -> str:
    notes = {
        "245": "M 필드; 미기재 시 저장 불가",
        "250": "MA 필드; 판사항 있는 자료에만 적용",
        "100": "O 필드; KCR4 비적용 기관은 미사용이 원칙",
        "856": "MA 필드; 원문 제공 자료에만 적용",
        "650": "O 필드; 통제 어휘 인프라 보유 기관만 적용 가능",
        "653": "O 필드; 비통제 색인어; 650 대체 또는 병행 사용",
    }
    return notes.get(tag, "")


def analyze_institution_quality(df: pd.DataFrame) -> pd.DataFrame:
    """기관별 주요 필드 출현율 분석 — 논문 표 4"""
    # 소장 건수 기준 상위 기관 선정
    inst_counts = df.groupby("library_name").size().sort_values(ascending=False)
    top_insts = inst_counts.head(TOP_N_INSTITUTIONS).index.tolist()
    df_top = df[df["library_name"].isin(top_insts)].copy()

    # 분석 대상 태그 (표 4 기준)
    table4_tags = ["100", "250", "650", "653", "700", "856"]

    rows = []
    for inst in top_insts:
        sub = df_top[df_top["library_name"] == inst]
        n = len(sub)
        row = {
            "기관명": inst,
            "소장건수": n,
            "비율(%)": round(n / len(df) * 100, 2),
        }
        for tag in table4_tags:
            col = f"has_{tag}"
            if col in sub.columns:
                rate = sub[col].sum() / n * 100
                row[f"{tag}({TAG_LABELS[tag]}) 출현율(%)"] = round(rate, 1)
        rows.append(row)

    result = pd.DataFrame(rows)
    return result


def save_results(field_freq: pd.DataFrame, inst_quality: pd.DataFrame):
    # 논문 표 3
    field_freq.to_csv(RESULTS_DIR / "table3_field_frequency.csv",
                      index=False, encoding='utf-8-sig')
    field_freq.to_csv(PROCESSED_DIR / "field_frequency.csv",
                      index=False, encoding='utf-8-sig')

    # 논문 표 4
    inst_quality.to_csv(RESULTS_DIR / "table4_institution.csv",
                        index=False, encoding='utf-8-sig')
    inst_quality.to_csv(PROCESSED_DIR / "institution_quality.csv",
                        index=False, encoding='utf-8-sig')

    print(f"\n[표 3 — 태그별 출현 빈도]")
    print(field_freq[["태그", "필드명", "필드유형", "출현건수", "출현율(%)"]].to_string(index=False))

    print(f"\n[표 4 — 기관별 품질 분석 (상위 {TOP_N_INSTITUTIONS}개)]")
    print(inst_quality.to_string(index=False))


def main():
    df = load_data()
    field_freq = analyze_field_frequency(df)
    inst_quality = analyze_institution_quality(df)
    save_results(field_freq, inst_quality)
    print("\n완료.")


if __name__ == "__main__":
    main()
