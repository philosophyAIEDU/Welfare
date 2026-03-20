"""
탭 2: 1인망 연결망 관리 화면
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any, List

from .dialogs import NetworkDialog
from ..core.database import Database


class NetworkTab(ttk.Frame):
    """1인망 연결망 관리 탭"""

    def __init__(self, parent: tk.Widget, db: Database):
        super().__init__(parent)
        self.db = db
        self.selected_beneficiary_id: Optional[int] = None
        self.selected_beneficiary_name: str = ""

        self._build_ui()
        self.refresh_beneficiary_list()

    def _build_ui(self) -> None:
        """UI 구성"""
        # 메인 PanedWindow
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 좌측: 대상자 선택 리스트
        left_frame = ttk.LabelFrame(paned, text="대상자 선택", padding=5)
        paned.add(left_frame, weight=1)

        # 검색
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(search_frame, text="🔍").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_changed)
        ttk.Entry(search_frame, textvariable=self.search_var, width=20).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # 대상자 리스트
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.beneficiary_listbox = tk.Listbox(list_frame, font=("맑은 고딕", 10),
                                              activestyle="none")
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                  command=self.beneficiary_listbox.yview)
        self.beneficiary_listbox.configure(yscrollcommand=scrollbar.set)
        self.beneficiary_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.beneficiary_listbox.bind("<<ListboxSelect>>", self._on_beneficiary_select)

        # 우측: 연결망 목록
        right_frame = ttk.LabelFrame(paned, text="연결망 정보", padding=5)
        paned.add(right_frame, weight=3)

        # 선택된 대상자 정보
        self.info_label = ttk.Label(right_frame, text="대상자를 선택해주세요",
                                    font=("맑은 고딕", 12, "bold"))
        self.info_label.pack(fill=tk.X, pady=(0, 10))

        # 버튼
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(btn_frame, text="➕ 연결망 추가", command=self.add_network).pack(
            side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="✏️ 수정", command=self.edit_network).pack(
            side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🗑️ 삭제", command=self.delete_network).pack(
            side=tk.LEFT, padx=2)

        # 연결망 테이블
        columns = ("contact_name", "relationship", "phone", "role", "visit_cycle", "note")
        self.network_tree = ttk.Treeview(right_frame, columns=columns,
                                         show="headings", selectmode="browse")

        headings = {
            "contact_name": ("이름", 80),
            "relationship": ("관계", 80),
            "phone": ("연락처", 110),
            "role": ("역할", 80),
            "visit_cycle": ("방문주기", 80),
            "note": ("비고", 150),
        }
        for col, (text, width) in headings.items():
            self.network_tree.heading(col, text=text)
            self.network_tree.column(col, width=width)

        # 짝수/홀수 행 색상
        self.network_tree.tag_configure("even", background="#FFFFFF")
        self.network_tree.tag_configure("odd", background="#F0F4FA")

        net_scroll = ttk.Scrollbar(right_frame, orient=tk.VERTICAL,
                                   command=self.network_tree.yview)
        self.network_tree.configure(yscrollcommand=net_scroll.set)
        self.network_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        net_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.network_tree.bind("<Double-1>", lambda e: self.edit_network())

        # 하단 요약
        self.summary_label = ttk.Label(right_frame, text="",
                                       font=("맑은 고딕", 9), foreground="#666666")
        self.summary_label.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))

    def refresh_beneficiary_list(self) -> None:
        """대상자 리스트 갱신"""
        self.all_beneficiaries = self.db.get_all_beneficiaries()
        self._filter_beneficiary_list()

    def _filter_beneficiary_list(self) -> None:
        """대상자 리스트 필터링"""
        search = self.search_var.get().lower()
        self.beneficiary_listbox.delete(0, tk.END)

        network_counts = self.db.get_all_network_counts()

        for b in self.all_beneficiaries:
            name = b.get("name", "")
            if search and search not in name.lower() and search not in str(b.get("phone", "")).lower():
                continue
            count = network_counts.get(b["id"], 0)
            warning = " ⚠️" if count == 0 else ""
            display = f"{name} ({b.get('manager', '')}) [{count}명]{warning}"
            self.beneficiary_listbox.insert(tk.END, display)

            # 연결망 없는 경우 빨간색
            if count == 0:
                self.beneficiary_listbox.itemconfig(tk.END, fg="#F44336")

    def _on_search_changed(self, *args) -> None:
        """검색어 변경"""
        self._filter_beneficiary_list()

    def _on_beneficiary_select(self, event) -> None:
        """대상자 선택"""
        selection = self.beneficiary_listbox.curselection()
        if not selection:
            return

        # 검색 필터링 적용된 목록에서 인덱스 계산
        search = self.search_var.get().lower()
        filtered = []
        for b in self.all_beneficiaries:
            name = b.get("name", "")
            if search and search not in name.lower() and search not in str(b.get("phone", "")).lower():
                continue
            filtered.append(b)

        idx = selection[0]
        if idx < len(filtered):
            b = filtered[idx]
            self.selected_beneficiary_id = b["id"]
            self.selected_beneficiary_name = b.get("name", "")
            self.info_label.config(
                text=f"[{self.selected_beneficiary_name}] 연결망  |  "
                     f"전화: {b.get('phone', '')}  |  담당: {b.get('manager', '')}"
            )
            self._refresh_networks()

    def _refresh_networks(self) -> None:
        """연결망 목록 갱신"""
        for item in self.network_tree.get_children():
            self.network_tree.delete(item)

        if not self.selected_beneficiary_id:
            self.summary_label.config(text="")
            return

        networks = self.db.get_networks_by_beneficiary(self.selected_beneficiary_id)

        role_counts: Dict[str, int] = {}
        for idx, net in enumerate(networks):
            values = (
                net.get("contact_name", ""),
                net.get("relationship", ""),
                net.get("phone", ""),
                net.get("role", ""),
                net.get("visit_cycle", ""),
                net.get("note", ""),
            )
            tag = "even" if idx % 2 == 0 else "odd"
            self.network_tree.insert("", tk.END, values=values, tags=(tag,))

            role = net.get("role", "기타")
            role_counts[role] = role_counts.get(role, 0) + 1

        # 요약
        total = len(networks)
        parts = [f"{r} {c}명" for r, c in role_counts.items()]
        summary = f"연결망 요약: {', '.join(parts)} (총 {total}명)" if parts else "연결망 없음"
        self.summary_label.config(text=summary)

    def _get_selected_network_id(self) -> Optional[int]:
        """선택된 연결망 ID 반환"""
        selection = self.network_tree.selection()
        if not selection:
            return None

        idx = self.network_tree.index(selection[0])
        networks = self.db.get_networks_by_beneficiary(self.selected_beneficiary_id)
        if 0 <= idx < len(networks):
            return networks[idx]["id"]
        return None

    # ==================== CRUD ====================

    def add_network(self) -> None:
        """연결망 추가"""
        if not self.selected_beneficiary_id:
            messagebox.showinfo("알림", "대상자를 먼저 선택해주세요.")
            return

        dialog = NetworkDialog(
            self.winfo_toplevel(),
            title="연결망 추가",
            beneficiary_name=self.selected_beneficiary_name
        )
        if dialog.result:
            try:
                dialog.result["beneficiary_id"] = self.selected_beneficiary_id
                self.db.add_network(dialog.result)
                self._refresh_networks()
                self._filter_beneficiary_list()
            except Exception as e:
                messagebox.showerror("오류", f"연결망 추가 중 오류가 발생했습니다.\n{str(e)}")

    def edit_network(self) -> None:
        """연결망 수정"""
        net_id = self._get_selected_network_id()
        if not net_id:
            messagebox.showinfo("알림", "수정할 연결망을 선택해주세요.")
            return

        data = self.db.get_network(net_id)
        if not data:
            return

        dialog = NetworkDialog(
            self.winfo_toplevel(),
            title="연결망 수정",
            data=data,
            beneficiary_name=self.selected_beneficiary_name
        )
        if dialog.result:
            try:
                self.db.update_network(net_id, dialog.result)
                self._refresh_networks()
            except Exception as e:
                messagebox.showerror("오류", f"연결망 수정 중 오류가 발생했습니다.\n{str(e)}")

    def delete_network(self) -> None:
        """연결망 삭제"""
        net_id = self._get_selected_network_id()
        if not net_id:
            messagebox.showinfo("알림", "삭제할 연결망을 선택해주세요.")
            return

        if messagebox.askyesno("삭제 확인", "이 연결망을 삭제하시겠습니까?"):
            try:
                self.db.delete_network(net_id)
                self._refresh_networks()
                self._filter_beneficiary_list()
            except Exception as e:
                messagebox.showerror("오류", f"삭제 중 오류가 발생했습니다.\n{str(e)}")
