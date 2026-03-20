"""
탭 1: 대상자 관리 화면 (메인)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Dict, Any, List

from .filterable_table import FilterableTable
from .dialogs import (
    BeneficiaryDialog, ColumnMappingDialog, ExportDialog
)
from ..core.database import Database
from ..core.data_loader import read_excel_file, auto_map_columns, convert_rows_to_dicts
from ..core.data_exporter import (
    export_current_view, export_by_manager, export_with_networks,
    generate_filename, BENEFICIARY_COLUMNS
)
from ..core.config import Config


class BeneficiaryTab(ttk.Frame):
    """대상자 관리 탭"""

    def __init__(self, parent: tk.Widget, db: Database, config: Config,
                 status_callback=None):
        super().__init__(parent)
        self.db = db
        self.config = config
        self.status_callback = status_callback
        self.selected_manager: Optional[str] = None
        self._search_after_id = None

        self._build_ui()
        self.refresh_data()

    def _build_ui(self) -> None:
        """UI 구성"""
        # 상단 툴바
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="📁 엑셀 불러오기", command=self.import_excel).pack(
            side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="➕ 대상자 추가", command=self.add_beneficiary).pack(
            side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ 수정", command=self.edit_beneficiary).pack(
            side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ 삭제", command=self.delete_beneficiary).pack(
            side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📥 엑셀 내보내기", command=self.export_excel).pack(
            side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔄 새로고침", command=self.refresh_data).pack(
            side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # 필터 초기화 버튼
        ttk.Button(toolbar, text="필터 초기화", command=self.clear_filters).pack(
            side=tk.LEFT, padx=2)

        # 검색
        ttk.Label(toolbar, text="🔍 통합검색:").pack(side=tk.LEFT, padx=(15, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_changed)
        self.search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.LEFT)

        # 메인 영역: 좌측 담당자 목록 + 우측 테이블
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 좌측: 담당자 목록
        left_frame = ttk.LabelFrame(paned, text="담당자 목록", padding=5)
        paned.add(left_frame, weight=1)

        self.manager_listbox = tk.Listbox(left_frame, font=("맑은 고딕", 10),
                                          activestyle="none")
        self.manager_listbox.pack(fill=tk.BOTH, expand=True)
        self.manager_listbox.bind("<<ListboxSelect>>", self._on_manager_select)

        # 우측: 테이블
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=4)

        # 테이블 열 정의
        table_columns = [
            ("담당자", "manager", 80),
            ("이름", "name", 80),
            ("전화번호", "phone", 110),
            ("주소", "address", 150),
            ("서비스", "service_type", 100),
            ("돌봄등급", "grade", 80),
            ("상태", "status", 60),
            ("비고", "note", 150),
        ]

        self.table = FilterableTable(
            right_frame,
            columns=table_columns,
            on_select=self._on_row_select,
            on_double_click=self._on_row_double_click,
            show_id=True
        )
        self.table.pack(fill=tk.BOTH, expand=True)

        # 빈 화면 안내 레이블
        self.empty_label = ttk.Label(
            right_frame,
            text="엑셀 파일을 불러오거나 대상자를 추가해주세요 📋",
            font=("맑은 고딕", 12),
            foreground="#888888"
        )

    def refresh_data(self) -> None:
        """데이터 새로고침"""
        try:
            data = self.db.get_all_beneficiaries()
            self.table.set_data(data)
            self._refresh_manager_list()
            self._update_status()

            # 빈 화면 안내
            if not data:
                self.empty_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            else:
                self.empty_label.place_forget()

        except Exception as e:
            messagebox.showerror("오류", f"데이터를 불러오는 중 오류가 발생했습니다.\n{str(e)}")

    def _refresh_manager_list(self) -> None:
        """담당자 목록 갱신"""
        self.manager_listbox.delete(0, tk.END)
        data = self.db.get_all_beneficiaries()
        total = len(data)
        self.manager_listbox.insert(tk.END, f"📋 전체 ({total}명)")

        managers = self.db.get_managers()
        for mgr in managers:
            count = len(self.db.get_beneficiaries_by_manager(mgr))
            self.manager_listbox.insert(tk.END, f"👤 {mgr} ({count}명)")

    def _on_manager_select(self, event) -> None:
        """담당자 선택"""
        selection = self.manager_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        if idx == 0:
            # 전체
            self.selected_manager = None
            data = self.db.get_all_beneficiaries()
        else:
            managers = self.db.get_managers()
            if idx - 1 < len(managers):
                self.selected_manager = managers[idx - 1]
                data = self.db.get_beneficiaries_by_manager(self.selected_manager)
            else:
                return

        self.table.set_data(data)
        self._update_status()

    def _on_search_changed(self, *args) -> None:
        """검색어 변경 (300ms 디바운스)"""
        if self._search_after_id:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(300, self._apply_search)

    def _apply_search(self) -> None:
        """검색 적용"""
        self.table.set_search(self.search_var.get())
        self._update_status()

    def clear_filters(self) -> None:
        """필터 초기화"""
        self.table.clear_all_filters()
        self.search_var.set("")
        self.selected_manager = None
        if self.manager_listbox.size() > 0:
            self.manager_listbox.selection_clear(0, tk.END)
            self.manager_listbox.selection_set(0)
        self.refresh_data()

    def _update_status(self) -> None:
        """상태바 업데이트"""
        if self.status_callback:
            total = self.table.get_total_count()
            filtered = self.table.get_filtered_count()
            managers = len(self.db.get_managers())

            # 서비스별 통계
            service_stats = {}
            for row in self.table.all_data:
                svc = row.get("service_type", "")
                if svc:
                    service_stats[svc] = service_stats.get(svc, 0) + 1

            self.status_callback(total, filtered, managers, service_stats)

    def _on_row_select(self, event) -> None:
        """행 선택"""
        pass

    def _on_row_double_click(self, event) -> None:
        """행 더블클릭 → 수정"""
        self.edit_beneficiary()

    # ==================== CRUD ====================

    def add_beneficiary(self) -> None:
        """대상자 추가"""
        managers = self.db.get_managers()
        dialog = BeneficiaryDialog(
            self.winfo_toplevel(),
            title="대상자 추가",
            managers=managers,
            check_duplicate_phone=self.db.check_duplicate_phone
        )
        if dialog.result:
            try:
                self.db.add_beneficiary(dialog.result)
                self.refresh_data()
                self._update_status()
            except Exception as e:
                messagebox.showerror("오류", f"대상자 추가 중 오류가 발생했습니다.\n{str(e)}")

    def edit_beneficiary(self) -> None:
        """대상자 수정"""
        selected = self.table.get_selected_data()
        if not selected:
            messagebox.showinfo("알림", "수정할 대상자를 선택해주세요.")
            return
        if len(selected) > 1:
            messagebox.showinfo("알림", "1명만 선택해주세요.")
            return

        data = selected[0]
        managers = self.db.get_managers()
        dialog = BeneficiaryDialog(
            self.winfo_toplevel(),
            title="대상자 수정",
            data=data,
            managers=managers,
            check_duplicate_phone=self.db.check_duplicate_phone
        )
        if dialog.result:
            try:
                self.db.update_beneficiary(data["id"], dialog.result)
                self.refresh_data()
            except Exception as e:
                messagebox.showerror("오류", f"대상자 수정 중 오류가 발생했습니다.\n{str(e)}")

    def delete_beneficiary(self) -> None:
        """대상자 삭제 (소프트 삭제)"""
        selected = self.table.get_selected_data()
        if not selected:
            messagebox.showinfo("알림", "삭제할 대상자를 선택해주세요.")
            return

        count = len(selected)
        msg = f"{count}명의 대상자를 삭제하시겠습니까?\n(상태가 '삭제됨'으로 변경됩니다)"
        if messagebox.askyesno("삭제 확인", msg):
            try:
                for item in selected:
                    self.db.delete_beneficiary(item["id"])
                self.refresh_data()
            except Exception as e:
                messagebox.showerror("오류", f"삭제 중 오류가 발생했습니다.\n{str(e)}")

    # ==================== 엑셀 불러오기 ====================

    def import_excel(self) -> None:
        """엑셀 파일 불러오기"""
        file_path = filedialog.askopenfilename(
            title="엑셀 파일 선택",
            filetypes=[
                ("엑셀 파일", "*.xlsx *.xls"),
                ("CSV 파일", "*.csv"),
                ("모든 파일", "*.*")
            ],
            initialdir=self.config.get("last_file_path", "")
        )
        if not file_path:
            return

        self.config.set("last_file_path", file_path)

        try:
            columns, data = read_excel_file(file_path)
        except Exception as e:
            messagebox.showerror(
                "파일 읽기 오류",
                f"엑셀 파일을 읽을 수 없습니다.\n"
                f"파일이 다른 프로그램에서 열려 있지 않은지 확인해주세요.\n\n"
                f"오류: {str(e)}"
            )
            return

        # 자동 매핑
        saved_mapping = self.config.get_column_mapping()
        auto_mapping = auto_map_columns(columns, saved_mapping)

        # 매핑 다이얼로그
        dialog = ColumnMappingDialog(
            self.winfo_toplevel(),
            file_columns=columns,
            auto_mapping=auto_mapping
        )

        if dialog.result is None:
            return

        mapping = dialog.result
        # 매핑 설정 저장
        self.config.set_column_mapping(mapping)

        # 데이터 변환
        rows = convert_rows_to_dicts(columns, data, mapping)
        if not rows:
            messagebox.showinfo("알림", "불러올 데이터가 없습니다.\n열 매핑을 확인해주세요.")
            return

        # 추가/교체 선택
        mode = messagebox.askyesnocancel(
            "불러오기 모드",
            f"{len(rows)}건의 데이터를 불러옵니다.\n\n"
            f"예: 기존 데이터에 추가\n"
            f"아니오: 기존 데이터 교체 (삭제 후 추가)\n"
            f"취소: 불러오기 취소"
        )

        if mode is None:
            return

        try:
            if mode is False:
                # 교체 모드
                self.db.clear_all_beneficiaries()

            count = self.db.bulk_insert_beneficiaries(rows)
            messagebox.showinfo("완료", f"{count}건의 데이터를 불러왔습니다.")
            self.refresh_data()
        except Exception as e:
            messagebox.showerror("오류", f"데이터 불러오기 중 오류가 발생했습니다.\n{str(e)}")

    # ==================== 엑셀 내보내기 ====================

    def export_excel(self) -> None:
        """엑셀 내보내기"""
        dialog = ExportDialog(self.winfo_toplevel())
        if not dialog.result:
            return

        mode = dialog.result
        default_name = generate_filename()

        file_path = filedialog.asksaveasfilename(
            title="엑셀 파일 저장",
            defaultextension=".xlsx",
            initialfile=default_name,
            filetypes=[("엑셀 파일", "*.xlsx")]
        )
        if not file_path:
            return

        try:
            if mode == "current":
                export_current_view(self.table.filtered_data, file_path)
            elif mode == "all":
                all_data = self.db.get_all_beneficiaries()
                export_current_view(all_data, file_path)
            elif mode == "by_manager":
                all_data = self.db.get_all_beneficiaries()
                export_by_manager(all_data, file_path)
            elif mode == "with_network":
                all_data = self.db.get_all_beneficiaries()
                networks = {}
                for b in all_data:
                    networks[b["id"]] = self.db.get_networks_by_beneficiary(b["id"])
                export_with_networks(all_data, networks, file_path)

            messagebox.showinfo("완료", f"엑셀 파일이 저장되었습니다.\n{file_path}")
        except Exception as e:
            messagebox.showerror("오류", f"내보내기 중 오류가 발생했습니다.\n{str(e)}")
