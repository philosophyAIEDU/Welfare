"""
하단 상태바 위젯
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any


class StatusBar(ttk.Frame):
    """하단 상태바"""

    def __init__(self, parent: tk.Widget):
        super().__init__(parent, relief=tk.SUNKEN)

        self.status_var = tk.StringVar(value="준비")
        self.count_var = tk.StringVar(value="전체: 0명")
        self.manager_var = tk.StringVar(value="")
        self.service_var = tk.StringVar(value="")

        # 왼쪽: 상태 메시지
        ttk.Label(self, textvariable=self.count_var, font=("맑은 고딕", 9),
                  padding=(10, 3)).pack(side=tk.LEFT)
        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        ttk.Label(self, textvariable=self.manager_var, font=("맑은 고딕", 9),
                  padding=(5, 3)).pack(side=tk.LEFT)
        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        ttk.Label(self, textvariable=self.service_var, font=("맑은 고딕", 9),
                  padding=(5, 3)).pack(side=tk.LEFT)

        # 오른쪽: 상태
        ttk.Label(self, textvariable=self.status_var, font=("맑은 고딕", 9),
                  padding=(10, 3)).pack(side=tk.RIGHT)

    def update_status(self, text: str) -> None:
        """상태 메시지 업데이트"""
        self.status_var.set(text)

    def update_counts(self, total: int, filtered: int,
                      managers: int = 0, service_stats: Dict[str, int] = None) -> None:
        """카운트 업데이트"""
        if filtered != total:
            self.count_var.set(f"필터 적용 중: {filtered}명 / 전체 {total}명")
        else:
            self.count_var.set(f"전체: {total}명")

        if managers > 0:
            self.manager_var.set(f"담당자: {managers}명")

        if service_stats:
            parts = [f"{k}: {v}" for k, v in list(service_stats.items())[:4]]
            self.service_var.set(" | ".join(parts))
