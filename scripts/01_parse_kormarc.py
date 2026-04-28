"""
01_parse_kormarc.py
KORCIS 서지 데이터 XML 파싱 및 MARC 태그 추출

입력: data/raw/KORCIS_서지데이터_0*.xml
출력: data/processed/parsed_records.parquet (또는 .csv)
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
import json
import re
import sys

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# 분석 대상 MARC 태그 목록
TARGET_TAGS = {
    "100": "기본표목-개인명",
    "245": "서명저자사항",
    "250": "판사항",
    "260": "간사사항",
    "300": "형태사항",
    "600": "주제명부출-개인명",
    "650": "일반주제명",
    "651": "지명주제",
    "653": "비통제 색인어",
    "700": "부출표목-개인명",
    "856": "전자적 위치 및 접속",
}

# 전거 관련 태그 (0 식별기호 분석 대상)
AUTHORITY_TAGS = ["100", "700", "650"]

# 고문헌 특화 코드 (300$b 형태코드)
MORPHOLOGY_CODES = {
    "01": "삽화",
    "02": "광곽",
    "04": "계선",
    "07": "판구",
    "08": "어미",
}


def parse_marc_xml(xml_text: str) -> dict:
    """
    KORMARC XML 문자열을 파싱하여 태그별 존재 여부 및 값을 반환.
    반환 구조:
      {
        "tag_presence": {"100": True, "245": True, ...},
        "authority_nos": {"100": ["KAC..."], "700": [], ...},
        "urls_856": ["http://..."],
        "morphology_codes": ["02", "08", ...],
        "subfield_b250": "목판본",
      }
    """
    result = {
        "tag_presence": {tag: False for tag in TARGET_TAGS},
        "authority_nos": {tag: [] for tag in AUTHORITY_TAGS},
        "urls_856": [],
        "morphology_codes": [],
        "subfield_b250": None,
    }

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return result

    # 네임스페이스 처리 (KORCIS XML에 따라 조정 필요)
    ns_pattern = re.compile(r'\{[^}]*\}')

    for elem in root.iter():
        tag_local = ns_pattern.sub('', elem.tag)

        # datafield 처리
        if tag_local == 'datafield':
            tag_val = elem.attrib.get('tag', '')

            if tag_val in TARGET_TAGS:
                result["tag_presence"][tag_val] = True

            # 전거번호 (0 식별기호)
            if tag_val in AUTHORITY_TAGS:
                for sub in elem:
                    sub_local = ns_pattern.sub('', sub.tag)
                    if sub_local == 'subfield':
                        code = sub.attrib.get('code', '')
                        if code == '0' and sub.text:
                            result["authority_nos"][tag_val].append(sub.text.strip())

            # 856 URL
            if tag_val == '856':
                for sub in elem:
                    sub_local = ns_pattern.sub('', sub.tag)
                    if sub_local == 'subfield':
                        code = sub.attrib.get('code', '')
                        if code == 'u' and sub.text:
                            result["urls_856"].append(sub.text.strip())

            # 300$b 형태코드
            if tag_val == '300':
                for sub in elem:
                    sub_local = ns_pattern.sub('', sub.tag)
                    if sub_local == 'subfield':
                        code = sub.attrib.get('code', '')
                        if code == 'b' and sub.text:
                            for mc in MORPHOLOGY_CODES:
                                if mc in sub.text:
                                    result["morphology_codes"].append(mc)

            # 250$a 판종류
            if tag_val == '250':
                for sub in elem:
                    sub_local = ns_pattern.sub('', sub.tag)
                    if sub_local == 'subfield':
                        code = sub.attrib.get('code', '')
                        if code == 'a' and sub.text:
                            result["subfield_b250"] = sub.text.strip()

    return result


def process_files():
    xml_files = sorted(RAW_DIR.glob("*.xml"))
    if not xml_files:
        print(f"[오류] {RAW_DIR}/ 에 XML 파일이 없습니다.")
        print("공공데이터포털에서 KORCIS 서지 데이터를 다운로드하여 data/raw/ 에 위치시키세요.")
        sys.exit(1)

    print(f"총 {len(xml_files)}개 파일 처리 시작...")

    all_records = []

    for xml_file in xml_files:
        print(f"  처리 중: {xml_file.name}")
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
        except ET.ParseError as e:
            print(f"  [경고] 파싱 실패: {xml_file.name} — {e}")
            continue

        ns_pattern = re.compile(r'\{[^}]*\}')

        # 레코드 단위 순회 (KORCIS XML 구조에 따라 태그명 조정)
        for record in root.iter():
            tag_local = ns_pattern.sub('', record.tag)
            if tag_local not in ('record', 'Record', 'RECORD'):
                continue

            row = {}

            # 레코드키, 도서관부호, 도서관명 추출
            for child in record:
                child_local = ns_pattern.sub('', child.tag)
                if child_local in ('recordkey', 'RecordKey', '레코드키'):
                    row['record_key'] = child.text
                elif child_local in ('librarycode', 'LibraryCode', '도서관부호'):
                    row['library_code'] = child.text
                elif child_local in ('libraryname', 'LibraryName', '도서관명'):
                    row['library_name'] = child.text
                elif child_local in ('marc', 'Marc', 'MARC', '마크'):
                    marc_text = ET.tostring(child, encoding='unicode')
                    parsed = parse_marc_xml(marc_text)
                    # 태그 출현 여부
                    for tag, present in parsed["tag_presence"].items():
                        row[f'has_{tag}'] = present
                    # 전거번호 보유 여부
                    for tag in AUTHORITY_TAGS:
                        row[f'has_auth_{tag}'] = len(parsed["authority_nos"][tag]) > 0
                        row[f'auth_no_{tag}'] = "|".join(parsed["authority_nos"][tag])
                    # URL
                    row['urls_856'] = "|".join(parsed["urls_856"])
                    row['url_count'] = len(parsed["urls_856"])
                    # 형태코드
                    row['morphology_codes'] = "|".join(parsed["morphology_codes"])
                    # 판종류
                    row['edition_type'] = parsed["subfield_b250"]

            if row:
                all_records.append(row)

    if not all_records:
        print("[오류] 파싱된 레코드가 없습니다. XML 구조를 확인하세요.")
        sys.exit(1)

    df = pd.DataFrame(all_records)
    out_path = PROCESSED_DIR / "parsed_records.csv"
    df.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f"\n완료: {len(df):,}건 파싱 → {out_path}")
    return df


if __name__ == "__main__":
    process_files()
