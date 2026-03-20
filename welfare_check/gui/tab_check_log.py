"""
탭 3: 안부 확인 이력 관리 화면
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from .dialogs import CheckLogDialog
from ..core.database import Database
from ..core.data_exporter import export_check_logs, generate_filename


class CheckLogTab(ttk.Frame):
    """안부 확인 이력 탭"""

    def __init__(self, parent: tk.Widget, db: Database):
        super().__init__(parent)
        self.db = db
        self._build_ui()
        self.refresh_data()

    def _build_ui(self) -> None:
        """UI 구성"""
        # 상단 툴바
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="➕ 이력 추가", command=self.add_log).pack(
            side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ 수정", command=self.edit_log).pack(
            side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ 삭제", command=self.delete_log).pack(
            side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📥 이력 내보내기", command=self.export_logs).pack(
            side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔄 새로고침", command=self.refresh_data).pack(
            side=tk.LEFT, padx=2)

        # 필터 영역
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        ttk.Label(filter_frame, text="기간:").pack(side=tk.LEFT, padx=(0, 5))

        # 시작일
        self.start_date_var = tk.StringVar(
            value=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        ttk.Entry(filter_frame, textvariable=self.start_date_var, width=12).pack(
            side=tk.LEFT, padx=2)

        ttk.Label(filter_frame, text="~").pack(side=tk.LEFT, padx=5)

        # 종료일
        self.end_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(filter_frame, textvariable=self.end_date_var, width=12).pack(
            side=tk.LEFT, padx=2)

        ttk.Label(filter_frame, text="  결과:").pack(side=tk.LEFT, padx=(15, 5))
        self.result_filter_var = tk.StringVar(value="전체")
        result_combo = ttk.Combobox(
            filter_frame, textvariable=self.result_filter_var,
            values=["전체", "확인완료", "미응답", "부재중", "음성사서함"],
            width=10, state="readonly"
        )
        result_combo.pack(side=tk.LEFT, padx=2)

        ttk.Button(filter_frame, text="조회", command=self.refresh_data).pack(
            side=tk.LEFT, padx=10)

        # 테이블
        columns = ("check_date", "beneficiary_name", "check_type", "result",
                   "checked_by", "memo")
        self.log_tree = ttk.Treeview(self, columns=columns, show="headings",
                                     selectmode="browse")

        headings = {
            "check_date": ("날짜", 100),
            "beneficiary_name": ("대상자", 80),
            "check_type": ("확인방법", 80),
            "result": ("결과", 80),
            "checked_by": ("확인자", 80),
            "memo": ("메모", 200),
        }
        for col, (text, width) in headings.items():
            self.log_tree.heading(col, text=text)
            self.log_tree.column(col, width=width)

        self.log_tree.tag_configure("even", background="#FFFFFF")
        self.log_tree.tag_configure("odd", background="#F0F4FA")
        self.log_tree.tag_configure("no_response", foreground="#FF9800")
        self.log_tree.tag_configure("completed", foreground="#4CAF50")

        scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=scroll.set)
        self.log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=(0, 5))

        self.log_tree.bind("<Double-1>", lambda e: self.edit_log())

        # 빈 화면 안내
        self.empty_label = ttk.Label(
            self, text="안부 확인 이력이 없습니다. 이력을 추가해주세요.",
            font=("맑은 고딕", 12), foreground="#888888"
        )

    def refresh_data(self) -> None:
        """데이터 새로고침"""
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)

        try:
            logs = self.db.get_check_logs(
                start_date=self.start_date_var.get(),
                end_date=self.end_date_var.get(),
                result_filter=self.result_filter_var.get()
            )

            if not logs:
                self.empty_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            else:
                self.empty_label.place_forget()

            self.current_logs = logs
            for idx, log in enumerate(logs):
                values = (
                    log.get("check_date", ""),
                    log.get("beneficiary_name", ""),
                    log.get("check_type", ""),
                    log.get("result", ""),
                    log.get("checked_by", ""),
                    log.get("memo", ""),
                )
                tags = []
                tags.append("even" if idx % 2 == 0 else "odd")
                result = log.get("result", "")
                if result == "미응답" or result == "부재중":
                    tags.append("no_response")
                elif result == "확인완료":
                    tags.append("completed")

                self.log_tree.insert("", tk.END, values=values, tags=tuple(tags))

        except Exception as e:
            messagebox.showerror("오류", f"이력 조회 중 오류가 발생했습니다.\n{str(e)}")

    def _get_selected_log_id(self) -> Optional[int]:
        """선택된 이력 ID"""
        selection = self.log_tree.selection()
        if not selection:
            return None
        idx = self.log_tree.index(selection[0])
        if hasattr(self, 'current_logs') and 0 <= idx < len(self.current_logs):
            return self.current_logs[idx].get("id")
        return None

    def add_log(self) -> None:
        """이력 추가"""
        beneficiaries = self.db.get_all_beneficiaries()
        if not beneficiaries:
            messagebox.showinfo("알림", "먼저 대상자를 등록해주세요.")
            return

        dialog = CheckLogDialog(
            self.winfo_toplevel(),
            title="안부 확인 이력 추가",
            beneficiaries=beneficiaries
        )
        if dialog.result:
            try:
                self.db.add_check_log(dialog.result)
                self.refresh_data()
            except Exception as e:
                messagebox.showerror("오류", f"이력 추가 중 오류가 발생했습니다.\n{str(e)}")

    def edit_log(self) -> None:
        """이력 수정"""
        log_id = self._get_selected_log_id()
        if not log_id:
            messagebox.showinfo("알림", "수정할 이력을 선택해주세요.")
            return

        data = self.db.get_check_log(log_id)
        if not data:
            return

        beneficiaries = self.db.get_all_beneficiaries()
        dialog = CheckLogDialog(
            self.winfo_toplevel(),
            title="안부 확인 이력 수정",
            data=data,
            beneficiaries=beneficiaries
        )
        if dialog.result:
            try:
                self.db.update_check_log(log_id, dialog.result)
                self.refresh_data()
            except Exception as e:
                messagebox.showerror("오류", f"이력 수정 중 오류가 발생했습니다.\n{str(e)}")

    def delete_log(self) -> None:
        """이력 삭제"""
        log_id = self._get_selected_log_id()
        if not log_id:
            messagebox.showinfo("알림", "삭제할 이력을 선택해주세요.")
            return

        if messagebox.askyesno("삭제 확인", "이 이력을 삭제하시겠습니까?"):
            try:
                self.db.delete_check_log(log_id)
                self.refresh_data()
            except Exception as e:
                messagebox.showerror("오류", f"삭제 중 오류가 발생했습니다.\n{str(e)}")

    def export_logs(self) -> None:
        """이력 내보내기"""
        if not hasattr(self, 'current_logs') or not self.current_logs:
            messagebox.showinfo("알림", "내보낼 이력이 없습니다.")
            return

        file_path = filedialog.asksaveasfilename(
            title="이력 내보내기",
            defaultextension=".xlsx",
            initialfile=generate_filename("안부확인_이력"),
            filetypes=[("엑셀 파일", "*.xlsx")]
        )
        if not file_path:
            return

        try:
            export_check_logs(self.current_logs, file_path)
            messagebox.showinfo("완료", f"이력이 내보내졌습니다.\n{file_path}")
        except Exception as e:
            messagebox.showerror("오류", f"내보내기 중 오류가 발생했습니다.\n{str(e)}")
