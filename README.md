# KORCIS FAIR Analysis

**논문 제목**: FAIR 원칙에 따른 한국 고문헌 메타데이터 관리체계 진단  
**저널**: 한국기록관리학회지  
**저자**: 신은선  
**데이터 기준**: 2025년 7월 31일 공공데이터포털 공개 데이터  

---

## 개요

이 리포지터리는 위 논문의 분석 재현성(reproducibility) 확보를 위해 공개된 연구 데이터 및 분석 스크립트입니다.  
KORCIS(한국고문헌종합목록시스템) 전체 서지 데이터 567,212건을 대상으로 FAIR 원칙 준수도를 실증적으로 분석한 결과물을 담고 있습니다.

---

## 데이터 출처

원본 데이터는 국립중앙도서관이 공공데이터포털을 통해 공개한 KORCIS 서지 데이터입니다.

- **출처**: [공공데이터포털 — 한국고문헌종합목록시스템(KORCIS) 서지데이터](https://www.data.go.kr/data/15096231/fileData.do)  
- **파일 수**: 10개 (2025년 7월 31일 기준 공개본)  
- **총 레코드 수**: 567,212건  
- **참여 기관**: 142개 (국내 91, 해외 51)  
- **라이선스**: 공공누리 제1유형 (출처 표시)

> ⚠️ 원본 데이터 파일(XML)의 용량으로 인해 `data/raw/`에는 포함하지 않습니다.  
> 위 공공데이터포털 링크에서 직접 다운로드하실 수 있습니다.  
> 파일명 패턴: `KORCIS_서지데이터_0*.xml`

---

## 리포지터리 구조

```
korcis-fair-analysis/
├── README.md
├── data/
│   ├── raw/               # 원본 XML (용량 문제로 미포함, 위 출처에서 다운로드)
│   └── processed/
│       ├── field_frequency.csv        # KORMARC 태그별 출현 빈도 (논문 표 3)
│       ├── institution_quality.csv    # 기관별 주요 필드 출현율 (논문 표 4)
│       ├── authority_stats.csv        # 전거번호 기재 현황
│       └── url_analysis.csv           # 856 필드 URL 도메인 분석
├── scripts/
│   ├── 01_parse_kormarc.py            # XML 파싱 및 MARC 태그 추출
│   ├── 02_field_analysis.py           # 필드 출현 빈도 및 기관별 품질 분석
│   ├── 03_authority_analysis.py       # 전거번호·식별자 체계 분석
│   └── 04_fair_evaluation.py          # FAIR 항목별 판정 기준 적용
├── results/
│   ├── table3_field_frequency.csv     # 논문 표 3 원데이터
│   ├── table4_institution.csv         # 논문 표 4 원데이터
│   ├── table5_fair_evaluation.csv     # 논문 표 5 — 판정 근거 컬럼 포함
│   └── table6_comparison.csv          # 논문 표 6 — 해외 사례 비교
└── docs/
    ├── fair_criteria.md               # FAIR 15개 항목별 판정 기준 상세
    ├── kormarc_field_types.md         # KORMARC 필드 유형(필수/재량/해당시필수) 분류
    └── codebook.md                    # 분석 변수 설명
```

---

## 분석 환경

```
Python 3.11+
pandas >= 2.0
lxml >= 4.9
```

설치:
```bash
pip install pandas lxml
```

---

## 분석 실행 순서

```bash
# 1. 원본 XML을 data/raw/ 에 위치시킨 후 실행
python scripts/01_parse_kormarc.py

# 2. 필드 출현 빈도 및 기관별 품질 분석
python scripts/02_field_analysis.py

# 3. 전거번호 및 식별자 분석
python scripts/03_authority_analysis.py

# 4. FAIR 판정 기준 적용 및 결과 생성
python scripts/04_fair_evaluation.py
```

각 스크립트는 `data/processed/` 또는 `results/`에 결과를 저장합니다.

---

## 주요 결과 요약

| 항목 | 수치 |
|------|------|
| 총 분석 레코드 | 567,212건 |
| 참여 기관 | 142개 |
| 245(서명저자사항) 출현율 | 100.00% |
| 100(기본표목-개인명) 출현율 | 38.86% |
| 전거번호(0 식별기호) 기재율 | 0.55% 미만 |
| 국제 전거 URI(VIAF·Wikidata) 연계 | 0건 |
| 영구 식별자(DOI·ARK·PURL) 적용 | 0건 |
| FAIR 15개 항목 중 "적합" | 0개 (0%) |
| FAIR 15개 항목 중 "부분 적합" | 5개 (33.3%) |
| FAIR 15개 항목 중 "미흡·결여" | 10개 (66.7%) |

---

## FAIR 판정 기준

각 항목별 세부 판정 기준은 [`docs/fair_criteria.md`](docs/fair_criteria.md)를 참조하십시오.

---

## 인용

이 데이터 및 스크립트를 활용하는 경우 아래와 같이 인용해 주십시오.

```
신은선. (2026). FAIR 원칙에 따른 한국 고문헌 메타데이터 관리체계 진단 (게재 예정).
https://github.com/SHINEUNSUN1027/korcis-fair-analysis
```

---

## 문의

이슈 또는 Pull Request 환영합니다.
