"""
열별 필터 팝업 위젯 - 엑셀 스타일 필터 구현
"""

import tkinter as tk
from tkinter import ttk
from typing import Set, List, Callable, Optional


class FilterPopup:
    """
    엑셀 스타일 열별 필터 팝업
    체크박스 목록으로 값을 선택/해제하여 필터링
    """

    def __init__(
        self,
        parent: tk.Widget,
        column_name: str,
        unique_values: List[str],
        current_selection: Optional[Set[str]],
        on_apply: Callable[[str, Optional[Set[str]]], None],
        x: int = 0,
        y: int = 0
    ):
        """
        Args:
            parent: 부모 위젯
            column_name: 열 이름
            unique_values: 해당 열의 고유값 목록
            current_selection: 현재 선택된 값 (None이면 전체 선택)
            on_apply: 적용 콜백 (column_name, selected_values)
            x, y: 팝업 위치
        """
        self.parent = parent
        self.column_name = column_name
        self.unique_values = unique_values
        self.on_apply = on_apply

        # 팝업 창 생성
        self.popup = tk.Toplevel(parent)
        self.popup.title(f"필터: {column_name}")
        self.popup.geometry(f"280x400+{x}+{y}")
        self.popup.resizable(False, True)
        self.popup.transient(parent)

        # 외부 클릭 시 닫기
        self.popup.bind("<FocusOut>", self._on_focus_out)
        self.popup.focus_set()

        # 체크 변수 관리
        self.check_vars: dict = {}
        self.select_all_var = tk.BooleanVar(value=True)

        self._build_ui(current_selection)

    def _build_ui(self, current_selection: Optional[Set[str]]) -> None:
        """UI 구성"""
        main_frame = ttk.Frame(self.popup, padding=5)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 검색 영역
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(search_frame, text="🔍 검색:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_changed)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # 전체 선택 체크박스
        select_all_frame = ttk.Frame(main_frame)
        select_all_frame.pack(fill=tk.X)
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=2)

        self.select_all_cb = ttk.Checkbutton(
            select_all_frame, text="(전체 선택)",
            variable=self.select_all_var,
            command=self._on_select_all
        )
        self.select_all_cb.pack(anchor=tk.W)

        # 체크박스 목록 (스크롤 가능)
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        canvas = tk.Canvas(list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.checkbox_frame = ttk.Frame(canvas)

        self.checkbox_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.checkbox_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 마우스 휠 스크롤
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        # Linux 지원
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        self.canvas = canvas

        # 체크박스 생성
        all_selected = current_selection is None
        for val in self.unique_values:
            var = tk.BooleanVar(value=all_selected or (current_selection and val in current_selection))
            self.check_vars[val] = var
            cb = ttk.Checkbutton(
                self.checkbox_frame, text=val if val else "(빈 값)",
                variable=var, command=self._update_select_all
            )
            cb.pack(anchor=tk.W, padx=(10, 0))

        self._update_select_all()

        # 버튼 영역
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="적용", command=self._on_apply).pack(side=tk.LEFT, expand=True, padx=2)
        ttk.Button(btn_frame, text="초기화", command=self._on_reset).pack(side=tk.LEFT, expand=True, padx=2)
        ttk.Button(btn_frame, text="닫기", command=self.popup.destroy).pack(side=tk.LEFT, expand=True, padx=2)

    def _on_search_changed(self, *args) -> None:
        """검색어 변경 시 체크박스 목록 필터링"""
        search = self.search_var.get().lower()

        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()

        for val in self.unique_values:
            if search and search not in val.lower():
                continue
            var = self.check_vars.get(val)
            if var is None:
                continue
            cb = ttk.Checkbutton(
                self.checkbox_frame, text=val if val else "(빈 값)",
                variable=var, command=self._update_select_all
            )
            cb.pack(anchor=tk.W, padx=(10, 0))

    def _on_select_all(self) -> None:
        """전체 선택/해제"""
        checked = self.select_all_var.get()
        for var in self.check_vars.values():
            var.set(checked)

    def _update_select_all(self) -> None:
        """개별 체크박스 변경 시 전체 선택 상태 업데이트"""
        all_checked = all(var.get() for var in self.check_vars.values())
        self.select_all_var.set(all_checked)

    def _on_apply(self) -> None:
        """적용 버튼 클릭"""
        selected = {val for val, var in self.check_vars.items() if var.get()}

        # 전체 선택이면 필터 해제
        if len(selected) == len(self.unique_values):
            self.on_apply(self.column_name, None)
        else:
            self.on_apply(self.column_name, selected)

        self.popup.destroy()

    def _on_reset(self) -> None:
        """초기화 버튼 클릭"""
        for var in self.check_vars.values():
            var.set(True)
        self.select_all_var.set(True)
        self.on_apply(self.column_name, None)
        self.popup.destroy()

    def _on_focus_out(self, event) -> None:
        """포커스 아웃 시 닫기 (자식 위젯 제외)"""
        # 팝업 자체나 자식에 포커스가 남아있으면 무시
        try:
            focus_widget = self.popup.focus_get()
            if focus_widget and (focus_widget == self.popup or
                                str(focus_widget).startswith(str(self.popup))):
                return
        except Exception:
            pass
