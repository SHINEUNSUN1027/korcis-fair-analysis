"""
04_fair_evaluation.py
FAIR 원칙 15개 항목별 판정 기준 적용 및 결과 생성

입력: data/processed/*.csv (02, 03 스크립트 결과)
출력:
  - results/table5_fair_evaluation.csv  (논문 표 5 — 판정 근거 컬럼 포함)
  - results/table6_comparison.csv       (논문 표 6 — 해외 사례 비교)

판정 기준: docs/fair_criteria.md 참조
"""

import pandas as pd
import json
from pathlib import Path

PROCESSED_DIR = Path("data/processed")
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ── 판정 등급 상수 ─────────────────────────────────────────────
ADEQUATE = "적합"
PARTIAL = "부분 적합"
INADEQUATE = "미흡·결여"


def load_stats():
    """분석 결과 로드"""
    stats = {}

    # 필드 출현 빈도
    p = PROCESSED_DIR / "field_frequency.csv"
    if p.exists():
        df = pd.read_csv(p)
        for _, row in df.iterrows():
            stats[f"rate_{row['태그']}"] = row["출현율(%)"]

    # 전거 통계
    p = PROCESSED_DIR / "authority_stats.csv"
    if p.exists():
        df = pd.read_csv(p)
        for _, row in df.iterrows():
            tag = row["태그"]
            stats[f"auth_rate_{tag}"] = row.get("전거번호_보유율(%)", 0)
            stats[f"viaf_{tag}"] = row.get("VIAF_URI_건수", 0)
            stats[f"wikidata_{tag}"] = row.get("Wikidata_URI_건수", 0)

    # URL 분석
    p = PROCESSED_DIR / "url_analysis.csv"
    if p.exists():
        df = pd.read_csv(p)
        stats["url_total"] = len(df)
        stats["url_persistent"] = int(df["is_persistent"].sum()) if "is_persistent" in df.columns else 0
        stats["url_ip_count"] = int(df["is_ip_address"].sum()) if "is_ip_address" in df.columns else 0

    return stats


def evaluate_korcis(stats: dict) -> list:
    """
    KORCIS FAIR 15개 항목 평가.
    각 항목에 대해 판정 결과와 근거 지표를 명시적으로 반환.
    """
    total_records = 567212  # 전수 분석 건수

    evaluations = []

    # ── F 영역 ──────────────────────────────────────────────────

    evaluations.append({
        "항목": "F1",
        "영역": "Findable",
        "세부항목": "전 지구적으로 고유하고 영구적인 식별자 부여",
        "판정": INADEQUATE,
        "근거_정량": "영구 식별자(HTTP URI·DOI·ARK·PURL) 형식 레코드: 0건",
        "근거_정성": "001 필드 내부 제어번호 3가지 유형 혼재; 어느 것도 국제 통용 영구 식별자 형식 미충족",
        "개선방향": "서지 레코드 및 전거 개체에 HTTP URI 기반 영구 식별자 체계 도입",
    })

    evaluations.append({
        "항목": "F2",
        "영역": "Findable",
        "세부항목": "풍부한 메타데이터 기술",
        "판정": PARTIAL,
        "근거_정량": f"필수 필드(245·300·260) ≥99%; 선택 필드 650={stats.get('rate_650', 0):.2f}%, 856={stats.get('rate_856', 0):.2f}%",
        "근거_정성": "필수 필드 완성도 높으나 선택 필드 기관 간 편차 극심; 국제 표준 어휘 미적용으로 기계 가독성 낮음",
        "개선방향": "선택 필드 입력 지침 표준화; LCSH·VIAF 등 국제 통제 어휘 도입",
    })

    evaluations.append({
        "항목": "F3",
        "영역": "Findable",
        "세부항목": "메타데이터가 데이터 식별자를 명확히 포함",
        "판정": INADEQUATE,
        "근거_정량": f"856 필드 출현율: {stats.get('rate_856', 0):.2f}%; 영구 식별자 형식 URL: {stats.get('url_persistent', 0)}건",
        "근거_정성": "98.5% 레코드에 원문 링크 없음; 포함된 URL도 기관 내부 서버 임시 URL",
        "개선방향": "원문 객체에 DOI·ARK 등 영구 식별자 부여 및 856 필드 기재 확대",
    })

    evaluations.append({
        "항목": "F4",
        "영역": "Findable",
        "세부항목": "검색 가능한 자원에 등록 또는 인덱싱",
        "판정": PARTIAL,
        "근거_정량": "공공데이터포털 파일 배포 존재; OAI-PMH·API·SPARQL 엔드포인트: 0개",
        "근거_정성": "웹 검색 인터페이스 제공되나 기계적 수확 프로토콜 미지원으로 외부 인덱싱 제한",
        "개선방향": "OAI-PMH 또는 REST API 구축; 공개 메타데이터 수확 프로토콜 지원",
    })

    # ── A 영역 ──────────────────────────────────────────────────

    evaluations.append({
        "항목": "A1",
        "영역": "Accessible",
        "세부항목": "표준화된 통신 프로토콜로 식별자를 통해 검색 가능",
        "판정": PARTIAL,
        "근거_정량": "HTTPS 웹 인터페이스 제공; REST API·SPARQL: 0개",
        "근거_정성": "인간 접근(웹 검색)은 가능하나 식별자 기반 개별 레코드 기계적 조회 불가",
        "개선방향": "REST API 또는 SPARQL 엔드포인트 구축",
    })

    evaluations.append({
        "항목": "A1.1",
        "영역": "Accessible",
        "세부항목": "프로토콜이 개방적·무료·보편적",
        "판정": PARTIAL,
        "근거_정량": "HTTPS(오픈 프로토콜) 사용 확인",
        "근거_정성": "프로토콜 자체는 개방적이나 기계적 접근 수단 부재로 실질적 활용 제한",
        "개선방향": "A1과 연동 — 오픈 API 구축",
    })

    evaluations.append({
        "항목": "A1.2",
        "영역": "Accessible",
        "세부항목": "프로토콜이 인증·권한 절차 지원",
        "판정": PARTIAL,
        "근거_정량": "웹 검색 비회원 접근 가능; 공공데이터포털 다운로드 회원가입 필요",
        "근거_정성": "접근 정책 명시 문서 미확인; 조건부 공개 정책 불투명",
        "개선방향": "접근 정책 명시 및 라이선스 조건 문서화",
    })

    evaluations.append({
        "항목": "A2",
        "영역": "Accessible",
        "세부항목": "데이터 접근 불가 시에도 메타데이터 접근 가능",
        "판정": INADEQUATE,
        "근거_정량": "영구 식별자 없어 특정 레코드 지속적 참조 불가; 장기 보존 정책 미확인",
        "근거_정성": "공공데이터포털 파일 공개는 원문과 독립적이나 레코드 단위 접근 보장 구조 부재",
        "개선방향": "메타데이터 독립 저장소 및 영구 식별자 기반 장기 접근 보장 체계 마련",
    })

    # ── I 영역 ──────────────────────────────────────────────────

    evaluations.append({
        "항목": "I1",
        "영역": "Interoperable",
        "세부항목": "공식적이고 접근 가능하며 공유·적용 가능한 지식 표현 언어 사용",
        "판정": INADEQUATE,
        "근거_정량": "RDF·JSON-LD 형식 제공: 0건; KORMARC XML만 제공",
        "근거_정성": "텍스트 기반 평면 구조로 의미적 추론 불가; 이표기(朱熹·朱子) 동일 개체 인식 불가",
        "개선방향": "RDF 기반 온톨로지(BIBFRAME 또는 KoDEX) 전환",
    })

    evaluations.append({
        "항목": "I2",
        "영역": "Interoperable",
        "세부항목": "FAIR 준수 어휘를 사용하여 메타데이터 기술",
        "판정": INADEQUATE,
        "근거_정량": f"KAC 전거번호 연계: 1,600건(0.28%); LCSH·VIAF URI: 0건",
        "근거_정성": "국제 표준 통제 어휘 미적용; 판본 유형 자유 텍스트 혼용(木板本·목판본·木版本)",
        "개선방향": "LCSH·VIAF URI 등 국제 통제 어휘 도입; 판본 코드 통제화",
    })

    evaluations.append({
        "항목": "I3",
        "영역": "Interoperable",
        "세부항목": "정규화된 외부 참조 포함",
        "판정": INADEQUATE,
        "근거_정량": f"VIAF URI: {stats.get('viaf_100', 0) + stats.get('viaf_700', 0)}건; Wikidata URI: {stats.get('wikidata_100', 0) + stats.get('wikidata_700', 0)}건; LCNAF URI: 0건",
        "근거_정성": "국제 전거 시스템(VIAF·Wikidata·LCNAF)과의 owl:sameAs 연결 전무",
        "개선방향": "KAC 식별자를 VIAF·Wikidata URI와 owl:sameAs로 연결",
    })

    # ── R 영역 ──────────────────────────────────────────────────

    evaluations.append({
        "항목": "R1",
        "영역": "Reusable",
        "세부항목": "다양한 속성으로 풍부하게 기술",
        "판정": PARTIAL,
        "근거_정량": "필수 서지 필드 ≥99%; 데이터 생산 이력·출처 메타데이터: 미확인",
        "근거_정성": "기본 서지 정보 충실하나 데이터 생산 맥락·이력 정보 체계적 기술 없음",
        "개선방향": "provenance 메타데이터 체계 도입(PROV-O 등)",
    })

    evaluations.append({
        "항목": "R1.1",
        "영역": "Reusable",
        "세부항목": "명확하고 접근 가능한 데이터 사용 라이선스 보유",
        "판정": PARTIAL,
        "근거_정량": "공공데이터포털 배포본: 공공누리 제1유형 적용; 레코드 단위 라이선스 표시: 0건",
        "근거_정성": "데이터셋 수준 라이선스 존재하나 개별 레코드 메타데이터에 라이선스 필드 미기재",
        "개선방향": "레코드 단위 CC0 또는 CC BY 라이선스 명시",
    })

    evaluations.append({
        "항목": "R1.2",
        "영역": "Reusable",
        "세부항목": "상세한 출처 정보와 연결",
        "판정": INADEQUATE,
        "근거_정량": "소장 기관 식별 가능(도서관부호); 입력 일시·수정 이력: 미확인",
        "근거_정성": "기관 식별은 가능하나 데이터 생산·수정 이력의 체계적 기술 없음",
        "개선방향": "데이터 생산 일시·담당 기관 등 출처 이력 메타데이터 필드 추가",
    })

    evaluations.append({
        "항목": "R1.3",
        "영역": "Reusable",
        "세부항목": "도메인 관련 커뮤니티 표준 충족",
        "판정": PARTIAL,
        "근거_정량": "KORMARC 국내 표준 준수; BIBFRAME·EDM 정렬: 미이행",
        "근거_정성": "국내 도서관 표준(KORMARC)은 준수하나 국제 표준(BIBFRAME 2.0·EDM)과 미정렬",
        "개선방향": "BIBFRAME 2.0 또는 Europeana EDM과의 개념적 정렬 추진",
    })

    return evaluations


def build_table6_comparison() -> pd.DataFrame:
    """
    논문 표 6: KORCIS vs. 해외 사례 FAIR 비교
    각 기관의 판정 근거를 문헌·공식 문서 기반으로 명시
    """
    items = [
        ("F1", "영구 식별자"),
        ("F2", "풍부한 메타데이터"),
        ("F3", "데이터 식별자 포함"),
        ("F4", "인덱싱·등록"),
        ("A1", "프로토콜 기반 접근"),
        ("A2", "메타데이터 독립 접근"),
        ("I1", "공식 지식 표현 언어"),
        ("I2", "FAIR 준수 어휘"),
        ("I3", "외부 참조 연결"),
        ("R1", "풍부한 속성 기술"),
        ("R1.1", "라이선스 명시"),
        ("R1.2", "출처 정보"),
        ("R1.3", "커뮤니티 표준"),
    ]

    # 각 기관의 판정 (문헌 기반)
    # 근거 출처: Europeana(Isaac, 2013; Europeana n.d.a,b), NDL(国立国会図書館 n.d.), 중화고적자원고(장염, 2022; 허철, 2024)
    comparison = {
        "F1":   {"KORCIS": INADEQUATE, "Europeana": ADEQUATE,  "NDL": ADEQUATE,  "중화고적자원고": INADEQUATE,
                 "근거_Europeana": "HTTP URI 전 객체 부여(Isaac, 2013)", "근거_NDL": "https://id.ndl.go.jp/auth/entity/ URI 부여(国立国会図書館, n.d.)", "근거_중화고적": "HTTP URI 형식 영구 식별자 미확인(장염, 2022)"},
        "F2":   {"KORCIS": PARTIAL,    "Europeana": ADEQUATE,  "NDL": ADEQUATE,  "중화고적자원고": PARTIAL,
                 "근거_Europeana": "edm:ProvidedCHO 풍부한 속성 기술", "근거_NDL": "전거 데이터 RDF 형식 공개", "근거_중화고적": "기본 서지 사항만 제공(허철, 2024)"},
        "F3":   {"KORCIS": INADEQUATE, "Europeana": ADEQUATE,  "NDL": ADEQUATE,  "중화고적자원고": INADEQUATE,
                 "근거_Europeana": "edm:WebResource URI 명시", "근거_NDL": "디지털 컬렉션 URI 제공", "근거_중화고적": "원문 이미지만 제공; URI 없음"},
        "F4":   {"KORCIS": PARTIAL,    "Europeana": ADEQUATE,  "NDL": ADEQUATE,  "중화고적자원고": PARTIAL,
                 "근거_Europeana": "data.europeana.eu LOD; REST API", "근거_NDL": "SPARQL 엔드포인트(https://id.ndl.go.jp/auth/ndla)", "근거_중화고적": "웹 검색만; API 미지원"},
        "A1":   {"KORCIS": PARTIAL,    "Europeana": ADEQUATE,  "NDL": ADEQUATE,  "중화고적자원고": PARTIAL,
                 "근거_Europeana": "REST API JSON-LD 형식 제공(Europeana, n.d.b)", "근거_NDL": "SPARQL 엔드포인트 제공", "근거_중화고적": "API 미지원"},
        "A2":   {"KORCIS": INADEQUATE, "Europeana": ADEQUATE,  "NDL": ADEQUATE,  "중화고적자원고": PARTIAL,
                 "근거_Europeana": "CC0 메타데이터 독립 접근 보장", "근거_NDL": "전거 데이터 독립 RDF 공개", "근거_중화고적": "일부 메타데이터 접근 가능"},
        "I1":   {"KORCIS": INADEQUATE, "Europeana": ADEQUATE,  "NDL": ADEQUATE,  "중화고적자원고": INADEQUATE,
                 "근거_Europeana": "RDF/OWL 기반 EDM(Isaac, 2013)", "근거_NDL": "RDF 전거 데이터 공개", "근거_중화고적": "RDF 미제공(장염, 2022)"},
        "I2":   {"KORCIS": INADEQUATE, "Europeana": ADEQUATE,  "NDL": ADEQUATE,  "중화고적자원고": INADEQUATE,
                 "근거_Europeana": "Dublin Core·SKOS·OWL 재사용(Isaac, 2013)", "근거_NDL": "BIBFRAME 전환 추진", "근거_중화고적": "국제 표준 어휘 미적용"},
        "I3":   {"KORCIS": INADEQUATE, "Europeana": ADEQUATE,  "NDL": ADEQUATE,  "중화고적자원고": INADEQUATE,
                 "근거_Europeana": "VIAF·DBpedia·Wikidata owl:sameAs 연결(Europeana, n.d.b)", "근거_NDL": "VIAF URI owl:sameAs 연결(国立国会図書館, n.d.)", "근거_중화고적": "VIAF·Wikidata 연계 없음"},
        "R1":   {"KORCIS": PARTIAL,    "Europeana": ADEQUATE,  "NDL": ADEQUATE,  "중화고적자원고": PARTIAL,
                 "근거_Europeana": "edm:Agent·edm:TimeSpan·edm:Place 분리 기술", "근거_NDL": "전거 데이터 풍부한 속성", "근거_중화고적": "기본 속성만 제공"},
        "R1.1": {"KORCIS": PARTIAL,    "Europeana": ADEQUATE,  "NDL": PARTIAL,   "중화고적자원고": INADEQUATE,
                 "근거_Europeana": "메타데이터 CC0; 객체 저작권 상태 명시(Europeana, n.d.b)", "근거_NDL": "전거·서지 라이선스 상이 적용", "근거_중화고적": "라이선스 명시 미확인"},
        "R1.2": {"KORCIS": INADEQUATE, "Europeana": ADEQUATE,  "NDL": PARTIAL,   "중화고적자원고": INADEQUATE,
                 "근거_Europeana": "ore:Aggregation 출처 정보 포함", "근거_NDL": "부분 출처 이력 제공", "근거_중화고적": "출처 이력 미기술"},
        "R1.3": {"KORCIS": PARTIAL,    "Europeana": ADEQUATE,  "NDL": ADEQUATE,  "중화고적자원고": PARTIAL,
                 "근거_Europeana": "EDM — Dublin Core·OAI-ORE·SKOS 국제 표준 재사용", "근거_NDL": "BIBFRAME 국제 표준 전환 추진", "근거_중화고적": "국내 자체 기준; 국제 표준 미정렬"},
    }

    rows = []
    for item_code, label in items:
        if item_code in comparison:
            c = comparison[item_code]
            rows.append({
                "항목": item_code,
                "세부항목": label,
                "KORCIS": c["KORCIS"],
                "Europeana": c["Europeana"],
                "NDL(일본)": c["NDL"],
                "중화고적자원고(중국)": c["중화고적자원고"],
                "Europeana_판정근거": c.get("근거_Europeana", ""),
                "NDL_판정근거": c.get("근거_NDL", ""),
                "중화고적_판정근거": c.get("근거_중화고적", ""),
            })

    return pd.DataFrame(rows)


def main():
    stats = load_stats()

    # 표 5: KORCIS FAIR 준수도
    korcis_eval = evaluate_korcis(stats)
    df_table5 = pd.DataFrame(korcis_eval)
    df_table5.to_csv(RESULTS_DIR / "table5_fair_evaluation.csv",
                     index=False, encoding='utf-8-sig')

    # 표 6: 해외 사례 비교
    df_table6 = build_table6_comparison()
    df_table6.to_csv(RESULTS_DIR / "table6_comparison.csv",
                     index=False, encoding='utf-8-sig')

    # 요약 출력
    print("\n[표 5 — KORCIS FAIR 준수도 평가 결과]")
    counts = df_table5["판정"].value_counts()
    for level in [ADEQUATE, PARTIAL, INADEQUATE]:
        print(f"  {level}: {counts.get(level, 0)}개")

    print("\n[표 6 — 해외 사례 비교]")
    print(df_table6[["항목", "세부항목", "KORCIS", "Europeana", "NDL(일본)", "중화고적자원고(중국)"]].to_string(index=False))

    print("\n완료.")


if __name__ == "__main__":
    main()
