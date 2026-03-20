"""
데이터 관리 모듈 - 필터링, 검색, 정렬 비즈니스 로직
"""

from typing import List, Dict, Any, Optional, Set


class DataManager:
    """데이터 필터링/검색/정렬을 담당하는 클래스"""

    def __init__(self):
        self.all_data: List[Dict[str, Any]] = []
        self.active_filters: Dict[str, Set[str]] = {}
        self.search_text: str = ""
        self.sort_column: Optional[str] = None
        self.sort_reverse: bool = False

    def set_data(self, data: List[Dict[str, Any]]) -> None:
        """전체 데이터 설정"""
        self.all_data = data

    def set_filter(self, column: str, values: Set[str]) -> None:
        """특정 열에 필터 설정"""
        if values:
            self.active_filters[column] = values
        elif column in self.active_filters:
            del self.active_filters[column]

    def clear_filter(self, column: str) -> None:
        """특정 열의 필터 해제"""
        if column in self.active_filters:
            del self.active_filters[column]

    def clear_all_filters(self) -> None:
        """전체 필터 초기화"""
        self.active_filters.clear()
        self.search_text = ""

    def set_search(self, text: str) -> None:
        """검색어 설정"""
        self.search_text = text.strip()

    def set_sort(self, column: str) -> None:
        """정렬 설정 (같은 열 클릭 시 방향 토글)"""
        if self.sort_column == column:
            if self.sort_reverse:
                # 내림차순 → 정렬 해제
                self.sort_column = None
                self.sort_reverse = False
            else:
                # 오름차순 → 내림차순
                self.sort_reverse = True
        else:
            self.sort_column = column
            self.sort_reverse = False

    def get_filtered_data(self) -> List[Dict[str, Any]]:
        """필터, 검색, 정렬이 모두 적용된 데이터 반환"""
        result = self.all_data

        # 1. 열별 필터 적용 (AND 조건)
        if self.active_filters:
            filtered = []
            for row in result:
                visible = True
                for col, allowed_values in self.active_filters.items():
                    row_value = str(row.get(col, ""))
                    if row_value not in allowed_values:
                        visible = False
                        break
                if visible:
                    filtered.append(row)
            result = filtered

        # 2. 통합 검색 적용
        if self.search_text:
            search_lower = self.search_text.lower()
            searched = []
            for row in result:
                for value in row.values():
                    if search_lower in str(value).lower():
                        searched.append(row)
                        break
            result = searched

        # 3. 정렬 적용
        if self.sort_column:
            try:
                result = sorted(
                    result,
                    key=lambda x: str(x.get(self.sort_column, "")),
                    reverse=self.sort_reverse
                )
            except Exception:
                pass

        return result

    def get_unique_values(self, column: str) -> List[str]:
        """특정 열의 고유값 목록 반환 (필터 팝업용)"""
        values = set()
        for row in self.all_data:
            val = str(row.get(column, ""))
            if val:
                values.add(val)
        return sorted(values)

    def get_filter_status(self) -> str:
        """현재 필터 상태 문자열 반환"""
        filtered = self.get_filtered_data()
        total = len(self.all_data)
        current = len(filtered)

        if self.active_filters or self.search_text:
            return f"필터 적용 중: {current}명 / 전체 {total}명"
        return f"전체: {total}명"
