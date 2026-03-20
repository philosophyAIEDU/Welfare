"""
데이터 로더 모듈 - 엑셀/CSV 파일 읽기 및 열 매핑
"""

import os
from typing import List, Dict, Tuple, Optional, Any

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


# 프로그램 필드 목록 (매핑 대상)
FIELD_NAMES: Dict[str, str] = {
    "name": "이름",
    "phone": "전화번호",
    "address": "주소",
    "birth_date": "생년월일",
    "gender": "성별",
    "manager": "담당자",
    "service_type": "서비스",
    "grade": "돌봄등급",
    "note": "비고",
    "status": "상태",
}

# 자동 매핑 힌트 (엑셀 열 이름 → 프로그램 필드)
AUTO_MAPPING_HINTS: Dict[str, str] = {
    "성명": "name", "이름": "name", "대상자": "name", "대상자명": "name",
    "전화": "phone", "전화번호": "phone", "연락처": "phone", "휴대폰": "phone",
    "핸드폰": "phone", "HP": "phone",
    "주소": "address", "거주지": "address", "거주지주소": "address", "주소지": "address",
    "생년월일": "birth_date", "생일": "birth_date", "출생일": "birth_date",
    "성별": "gender",
    "담당자": "manager", "담당복지사": "manager", "담당": "manager",
    "서비스": "service_type", "서비스유형": "service_type", "적용서비스": "service_type",
    "서비스종류": "service_type",
    "등급": "grade", "돌봄등급": "grade", "돌봄 등급": "grade",
    "비고": "note", "특이사항": "note", "메모": "note", "참고": "note",
    "상태": "status",
}


def format_phone(phone: str) -> str:
    """
    전화번호 형식 자동 변환
    01012345678 → 010-1234-5678
    """
    if not phone:
        return ""
    # 숫자만 추출
    digits = "".join(c for c in str(phone) if c.isdigit())
    if len(digits) == 11 and digits.startswith("010"):
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    elif len(digits) == 10 and digits.startswith("02"):
        return f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
    elif len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    # 이미 하이픈이 있으면 그대로 반환
    if "-" in str(phone):
        return str(phone)
    return str(phone)


def read_excel_file(file_path: str) -> Tuple[List[str], List[List[Any]]]:
    """
    엑셀/CSV 파일 읽기

    Args:
        file_path: 파일 경로

    Returns:
        (열 이름 목록, 데이터 행 목록) 튜플

    Raises:
        Exception: 파일 읽기 실패 시
    """
    if not HAS_PANDAS:
        raise ImportError("pandas 라이브러리가 설치되지 않았습니다.")

    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == ".csv":
            df = pd.read_csv(file_path, encoding="utf-8")
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {ext}")
    except UnicodeDecodeError:
        # UTF-8 실패 시 cp949(한글 윈도우 기본)로 재시도
        df = pd.read_csv(file_path, encoding="cp949")

    columns = [str(c).strip() for c in df.columns.tolist()]
    # NaN을 빈 문자열로 변환
    df = df.fillna("")
    data = df.values.tolist()

    return columns, data


def auto_map_columns(file_columns: List[str], saved_mapping: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    열 자동 매핑 (파일 열 이름 → 프로그램 필드)

    Args:
        file_columns: 파일의 열 이름 목록
        saved_mapping: 이전에 저장된 매핑 설정

    Returns:
        {파일 열 이름: 프로그램 필드} 딕셔너리
    """
    mapping: Dict[str, str] = {}

    for col in file_columns:
        col_stripped = col.strip()

        # 1순위: 저장된 매핑에서 찾기
        if saved_mapping and col_stripped in saved_mapping:
            mapping[col_stripped] = saved_mapping[col_stripped]
            continue

        # 2순위: 자동 매핑 힌트에서 찾기
        matched = False
        for hint_key, field_name in AUTO_MAPPING_HINTS.items():
            if col_stripped == hint_key or hint_key in col_stripped:
                mapping[col_stripped] = field_name
                matched = True
                break

        if not matched:
            mapping[col_stripped] = ""  # 매핑 안 됨 (사용 안 함)

    return mapping


def convert_rows_to_dicts(
    columns: List[str],
    data: List[List[Any]],
    mapping: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    매핑 설정에 따라 행 데이터를 딕셔너리 목록으로 변환

    Args:
        columns: 파일 열 이름 목록
        data: 데이터 행 목록
        mapping: {파일 열 이름: 프로그램 필드} 매핑

    Returns:
        대상자 정보 딕셔너리 목록
    """
    result: List[Dict[str, Any]] = []

    for row in data:
        item: Dict[str, Any] = {}
        for i, col in enumerate(columns):
            field = mapping.get(col.strip(), "")
            if field and i < len(row):
                value = str(row[i]).strip() if row[i] != "" else ""
                if field == "phone":
                    value = format_phone(value)
                item[field] = value

        # 이름이 있는 행만 추가
        if item.get("name"):
            result.append(item)

    return result
