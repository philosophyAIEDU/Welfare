"""
필터링 가능한 Treeview 테이블 위젯
엑셀 스타일 열별 필터 + 정렬 + 검색 지원
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any, Optional, Set, Callable, Tuple

from .filter_popup import FilterPopup


class FilterableTable(ttk.Frame):
    """
    필터링/정렬 가능한 Treeview 기반 테이블 위젯

    각 열 헤더에 필터 버튼(▼)을 배치하고,
    클릭하면 체크박스 팝업으로 값 필터링 가능
    """

    def __init__(
        self,
        parent: tk.Widget,
        columns: List[Tuple[str, str, int]],
        on_select: Optional[Callable] = None,
        on_double_click: Optional[Callable] = None,
        show_id: bool = False
    ):
        """
        Args:
            parent: 부모 위젯
            columns: [(표시이름, 필드이름, 열너비), ...] 목록
            on_select: 행 선택 콜백
            on_double_click: 행 더블클릭 콜백
            show_id: ID 열 표시 여부
        """
        super().__init__(parent)

        self.columns = columns
        self.on_select_callback = on_select
        self.on_double_click_callback = on_double_click
        self.show_id = show_id

        # 데이터 관리
        self.all_data: List[Dict[str, Any]] = []
        self.filtered_data: List[Dict[str, Any]] = []
        self.active_filters: Dict[str, Set[str]] = {}
        self.search_text: str = ""
        self.sort_column: Optional[str] = None
        self.sort_reverse: bool = False

        # 색상 테마
        self.MAIN_COLOR = "#2E5090"
        self.SUB_COLOR = "#E3EBF6"
        self.BG_COLOR = "#F5F5F5"
        self.EVEN_ROW = "#FFFFFF"
        self.ODD_ROW = "#F0F4FA"
        self.SELECT_COLOR = "#B8D4F0"

        self._build_ui()

    def _build_ui(self) -> None:
        """UI 구성"""
        # 필터 버튼 프레임
        self.filter_btn_frame = ttk.Frame(self)
        self.filter_btn_frame.pack(fill=tk.X)

        # Treeview
        col_ids = [c[1] for c in self.columns]
        if self.show_id:
            col_ids = ["id"] + col_ids

        self.tree = ttk.Treeview(self, columns=col_ids, show="headings", selectmode="extended")

        # 스타일 설정
        style = ttk.Style()
        style.configure("Filter.Treeview", rowheight=28)
        style.configure("Filter.Treeview.Heading", font=("맑은 고딕", 10, "bold"))
        self.tree.configure(style="Filter.Treeview")

        # 태그 설정 (짝수/홀수 행)
        self.tree.tag_configure("even", background=self.EVEN_ROW)
        self.tree.tag_configure("odd", background=self.ODD_ROW)
        self.tree.tag_configure("selected_row", background=self.SELECT_COLOR)

        # ID 열 설정
        if self.show_id:
            self.tree.heading("id", text="번호", command=lambda: self._on_heading_click("id"))
            self.tree.column("id", width=50, minwidth=40, anchor=tk.CENTER)

        # 열 설정
        self.filter_buttons: Dict[str, tk.Button] = {}
        for display_name, field_name, width in self.columns:
            self.tree.heading(
                field_name,
                text=f"  {display_name} ▼",
                anchor=tk.W,
                command=lambda f=field_name: self._on_heading_click(f)
            )
            self.tree.column(field_name, width=width, minwidth=50)

        # 스크롤바
        v_scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        # 레이아웃
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        # 이벤트 바인딩
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-1>", self._on_click)

    def _on_heading_click(self, field_name: str) -> None:
        """열 헤더 클릭 - 필터 팝업 또는 정렬"""
        # 헤더 클릭 위치 확인
        region = self.tree.identify_region(
            self.tree.winfo_pointerx() - self.tree.winfo_rootx(),
            self.tree.winfo_pointery() - self.tree.winfo_rooty()
        )

        if region == "heading":
            # 클릭 위치 계산
            x = self.tree.winfo_rootx()
            y = self.tree.winfo_rooty()

            # 해당 열의 x 좌표 계산
            col_x = x
            col_ids = list(self.tree["columns"])
            for cid in col_ids:
                if cid == field_name:
                    break
                col_x += self.tree.column(cid, "width")

            self._show_filter_popup(field_name, col_x, y + 25)

    def _on_click(self, event) -> None:
        """테이블 클릭 이벤트"""
        region = self.tree.identify_region(event.x, event.y)
        if region == "heading":
            col = self.tree.identify_column(event.x)
            # '#1', '#2' 형태에서 인덱스 추출
            col_idx = int(col.replace("#", "")) - 1
            col_ids = list(self.tree["columns"])
            if 0 <= col_idx < len(col_ids):
                field_name = col_ids[col_idx]
                x = self.tree.winfo_rootx() + event.x
                y = self.tree.winfo_rooty() + event.y + 5
                self._show_filter_popup(field_name, x, y)
            return "break"

    def _show_filter_popup(self, field_name: str, x: int, y: int) -> None:
        """필터 팝업 표시"""
        # 고유값 목록 생성
        unique_values = sorted(set(
            str(row.get(field_name, "")) for row in self.all_data
            if str(row.get(field_name, ""))
        ))

        if not unique_values:
            # 값이 없으면 정렬만 수행
            self._toggle_sort(field_name)
            return

        current_selection = self.active_filters.get(field_name)

        FilterPopup(
            parent=self.winfo_toplevel(),
            column_name=field_name,
            unique_values=unique_values,
            current_selection=current_selection,
            on_apply=self._on_filter_apply,
            x=x, y=y
        )

    def _on_filter_apply(self, column_name: str, selected_values: Optional[Set[str]]) -> None:
        """필터 적용 콜백"""
        if selected_values is None:
            # 필터 해제
            if column_name in self.active_filters:
                del self.active_filters[column_name]
        else:
            self.active_filters[column_name] = selected_values

        self._update_heading_text(column_name)
        self.apply_filters()

    def _update_heading_text(self, column_name: str) -> None:
        """필터 상태에 따라 헤더 텍스트 업데이트"""
        for display_name, field_name, _ in self.columns:
            if field_name == column_name:
                if column_name in self.active_filters:
                    self.tree.heading(field_name, text=f"  {display_name} 🔽")
                else:
                    # 정렬 상태 확인
                    if self.sort_column == field_name:
                        arrow = " ▲" if not self.sort_reverse else " ▼"
                        self.tree.heading(field_name, text=f"  {display_name}{arrow}")
                    else:
                        self.tree.heading(field_name, text=f"  {display_name} ▼")
                break

    def _toggle_sort(self, field_name: str) -> None:
        """정렬 토글"""
        if self.sort_column == field_name:
            if self.sort_reverse:
                self.sort_column = None
                self.sort_reverse = False
            else:
                self.sort_reverse = True
        else:
            self.sort_column = field_name
            self.sort_reverse = False

        # 모든 헤더 텍스트 업데이트
        for display_name, fn, _ in self.columns:
            if fn == field_name and self.sort_column:
                arrow = " ▲" if not self.sort_reverse else " ▼"
                if fn in self.active_filters:
                    self.tree.heading(fn, text=f"  {display_name} 🔽{arrow}")
                else:
                    self.tree.heading(fn, text=f"  {display_name}{arrow}")
            elif fn in self.active_filters:
                self.tree.heading(fn, text=f"  {display_name} 🔽")
            else:
                self.tree.heading(fn, text=f"  {display_name} ▼")

        self.apply_filters()

    def set_data(self, data: List[Dict[str, Any]]) -> None:
        """테이블 데이터 설정"""
        self.all_data = data
        self.apply_filters()

    def apply_filters(self) -> None:
        """필터, 검색, 정렬을 적용하여 테이블 업데이트"""
        result = list(self.all_data)

        # 1. 열별 필터
        if self.active_filters:
            filtered = []
            for row in result:
                visible = True
                for col, allowed in self.active_filters.items():
                    if str(row.get(col, "")) not in allowed:
                        visible = False
                        break
                if visible:
                    filtered.append(row)
            result = filtered

        # 2. 통합 검색
        if self.search_text:
            search_lower = self.search_text.lower()
            searched = []
            for row in result:
                for value in row.values():
                    if search_lower in str(value).lower():
                        searched.append(row)
                        break
            result = searched

        # 3. 정렬
        if self.sort_column:
            try:
                result.sort(
                    key=lambda x: str(x.get(self.sort_column, "")),
                    reverse=self.sort_reverse
                )
            except Exception:
                pass

        self.filtered_data = result
        self._refresh_tree()

    def set_search(self, text: str) -> None:
        """검색어 설정"""
        self.search_text = text.strip()
        self.apply_filters()

    def clear_all_filters(self) -> None:
        """모든 필터 초기화"""
        self.active_filters.clear()
        self.search_text = ""
        self.sort_column = None
        self.sort_reverse = False

        # 모든 헤더 초기화
        for display_name, field_name, _ in self.columns:
            self.tree.heading(field_name, text=f"  {display_name} ▼")

        self.apply_filters()

    def _refresh_tree(self) -> None:
        """Treeview 갱신"""
        # 기존 데이터 삭제
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 새 데이터 삽입
        col_ids = list(self.tree["columns"])
        for idx, row in enumerate(self.filtered_data):
            values = []
            for cid in col_ids:
                values.append(str(row.get(cid, "")))
            tag = "even" if idx % 2 == 0 else "odd"
            self.tree.insert("", tk.END, values=values, tags=(tag,))

    def _on_select(self, event) -> None:
        """행 선택 이벤트"""
        if self.on_select_callback:
            self.on_select_callback(event)

    def _on_double_click(self, event) -> None:
        """행 더블클릭 이벤트"""
        if self.on_double_click_callback:
            region = self.tree.identify_region(event.x, event.y)
            if region == "cell":
                self.on_double_click_callback(event)

    def get_selected_data(self) -> List[Dict[str, Any]]:
        """선택된 행의 데이터 반환"""
        selected = []
        for item_id in self.tree.selection():
            idx = self.tree.index(item_id)
            if 0 <= idx < len(self.filtered_data):
                selected.append(self.filtered_data[idx])
        return selected

    def get_selected_ids(self) -> List[int]:
        """선택된 행의 ID 목록 반환"""
        ids = []
        for item in self.get_selected_data():
            if "id" in item:
                ids.append(item["id"])
        return ids

    def get_filtered_count(self) -> int:
        """현재 필터링된 행 수"""
        return len(self.filtered_data)

    def get_total_count(self) -> int:
        """전체 행 수"""
        return len(self.all_data)

    def get_status_text(self) -> str:
        """상태바 텍스트 반환"""
        total = self.get_total_count()
        filtered = self.get_filtered_count()
        if self.active_filters or self.search_text:
            return f"필터 적용 중: {filtered}명 / 전체 {total}명"
        return f"전체: {total}명"

    def has_active_filters(self) -> bool:
        """활성 필터 존재 여부"""
        return bool(self.active_filters) or bool(self.search_text)
