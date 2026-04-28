"""
03_authority_analysis.py
전거번호·식별자 체계 분석

입력: data/processed/parsed_records.csv
출력:
  - data/processed/authority_stats.csv
  - data/processed/url_analysis.csv
  - results/authority_summary.csv
"""

import pandas as pd
import re
from pathlib import Path
from urllib.parse import urlparse

PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# 영구 식별자 패턴
PERSISTENT_ID_PATTERNS = {
    "DOI": re.compile(r'https?://doi\.org/', re.I),
    "ARK": re.compile(r'/ark:/', re.I),
    "PURL": re.compile(r'https?://purl\.', re.I),
    "Handle": re.compile(r'https?://hdl\.handle\.net/', re.I),
}

# 국제 전거 URI 패턴
INTL_AUTHORITY_PATTERNS = {
    "VIAF": re.compile(r'viaf\.org', re.I),
    "Wikidata": re.compile(r'wikidata\.org', re.I),
    "LCNAF": re.compile(r'id\.loc\.gov', re.I),
    "ISNI": re.compile(r'isni\.org', re.I),
}

# 국내 전거 패턴
DOMESTIC_AUTHORITY_PATTERNS = {
    "NLK_KAC": re.compile(r'^KAC', re.I),
}


def load_data():
    path = PROCESSED_DIR / "parsed_records.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} 없음. 01_parse_kormarc.py를 먼저 실행하세요.")
    return pd.read_csv(path, low_memory=False)


def analyze_authority(df: pd.DataFrame) -> dict:
    """전거번호 기재 현황 분석"""
    total = len(df)
    stats = {}

    auth_tags = ["100", "700", "650"]
    for tag in auth_tags:
        has_tag_col = f"has_{tag}"
        auth_col = f"auth_no_{tag}"
        has_auth_col = f"has_auth_{tag}"

        if has_tag_col not in df.columns:
            continue

        df_with_tag = df[df[has_tag_col] == True]
        n_with_tag = len(df_with_tag)

        # 전거번호 보유
        n_has_auth = df_with_tag[has_auth_col].sum() if has_auth_col in df.columns else 0

        # 전거번호 유형 분류
        n_kac = 0
        n_viaf = 0
        n_wikidata = 0
        n_lcnaf = 0

        if auth_col in df.columns:
            auth_values = df_with_tag[auth_col].dropna()
            for val in auth_values:
                if not val:
                    continue
                for auth_no in str(val).split("|"):
                    auth_no = auth_no.strip()
                    if DOMESTIC_AUTHORITY_PATTERNS["NLK_KAC"].match(auth_no):
                        n_kac += 1
                    if INTL_AUTHORITY_PATTERNS["VIAF"].search(auth_no):
                        n_viaf += 1
                    if INTL_AUTHORITY_PATTERNS["Wikidata"].search(auth_no):
                        n_wikidata += 1
                    if INTL_AUTHORITY_PATTERNS["LCNAF"].search(auth_no):
                        n_lcnaf += 1

        stats[tag] = {
            "필드명": {"100": "기본표목-개인명", "700": "부출표목-개인명", "650": "일반주제명"}[tag],
            "필드보유건수": n_with_tag,
            "전거번호_보유건수": int(n_has_auth),
            "전거번호_보유율(%)": round(n_has_auth / n_with_tag * 100, 2) if n_with_tag > 0 else 0,
            "NLK_KAC_건수": n_kac,
            "VIAF_URI_건수": n_viaf,
            "Wikidata_URI_건수": n_wikidata,
            "LCNAF_URI_건수": n_lcnaf,
        }

    return stats


def analyze_urls(df: pd.DataFrame) -> pd.DataFrame:
    """856 필드 URL 분석"""
    if 'urls_856' not in df.columns:
        return pd.DataFrame()

    all_urls = []
    for val in df['urls_856'].dropna():
        for url in str(val).split("|"):
            url = url.strip()
            if url:
                all_urls.append(url)

    print(f"856 필드 URL 총 {len(all_urls):,}건 분석 중...")

    url_stats = []
    for url in all_urls:
        parsed = urlparse(url)
        domain = parsed.netloc

        pid_type = None
        for pid_name, pattern in PERSISTENT_ID_PATTERNS.items():
            if pattern.search(url):
                pid_type = pid_name
                break

        is_ip = bool(re.match(r'^\d+\.\d+\.\d+\.\d+', domain))

        url_stats.append({
            "url": url,
            "domain": domain,
            "is_ip_address": is_ip,
            "persistent_id_type": pid_type,
            "is_persistent": pid_type is not None,
        })

    df_urls = pd.DataFrame(url_stats)

    # 도메인별 집계
    domain_counts = df_urls.groupby("domain").size().sort_values(ascending=False).reset_index()
    domain_counts.columns = ["도메인", "건수"]

    print(f"\n[856 필드 URL 분석 요약]")
    print(f"  총 URL 건수: {len(all_urls):,}")
    print(f"  영구 식별자 형식(DOI·ARK·PURL·Handle): {df_urls['is_persistent'].sum():,}건")
    print(f"  IP 주소 직접 사용 URL: {df_urls['is_ip_address'].sum():,}건")
    print(f"\n  [도메인별 상위 10개]")
    print(domain_counts.head(10).to_string(index=False))

    return df_urls


def save_results(authority_stats: dict, url_df: pd.DataFrame):
    # 전거 통계
    auth_rows = []
    for tag, stat in authority_stats.items():
        row = {"태그": tag}
        row.update(stat)
        auth_rows.append(row)

    df_auth = pd.DataFrame(auth_rows)
    df_auth.to_csv(PROCESSED_DIR / "authority_stats.csv", index=False, encoding='utf-8-sig')
    df_auth.to_csv(RESULTS_DIR / "authority_summary.csv", index=False, encoding='utf-8-sig')

    print(f"\n[전거번호 기재 현황]")
    print(df_auth.to_string(index=False))

    # URL 분석 결과
    if not url_df.empty:
        url_df.to_csv(PROCESSED_DIR / "url_analysis.csv", index=False, encoding='utf-8-sig')


def main():
    df = load_data()
    authority_stats = analyze_authority(df)
    url_df = analyze_urls(df)
    save_results(authority_stats, url_df)
    print("\n완료.")


if __name__ == "__main__":
    main()
