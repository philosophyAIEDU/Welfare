"""
탭 4: 통계 화면
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, List, Tuple

from ..core.database import Database


class StatisticsTab(ttk.Frame):
    """통계 탭"""

    # 색상 테마
    MAIN_COLOR = "#2E5090"
    GREEN = "#4CAF50"
    ORANGE = "#FF9800"
    RED = "#F44336"
    BG = "#F5F5F5"
    CARD_BG = "#FFFFFF"

    def __init__(self, parent: tk.Widget, db: Database):
        super().__init__(parent)
        self.db = db
        self._build_ui()

    def _build_ui(self) -> None:
        """UI 구성"""
        # 스크롤 가능 영역
        canvas = tk.Canvas(self, highlightthickness=0, bg=self.BG)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview)
        self.scroll_frame = ttk.Frame(canvas)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scroll_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 마우스 휠 스크롤
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        # 새로고침 버튼
        ttk.Button(self.scroll_frame, text="🔄 통계 새로고침",
                   command=self.refresh_stats).pack(anchor=tk.W, padx=10, pady=10)

        # 통계 컨테이너
        self.stats_container = ttk.Frame(self.scroll_frame)
        self.stats_container.pack(fill=tk.BOTH, expand=True, padx=10)

    def refresh_stats(self) -> None:
        """통계 새로고침"""
        # 기존 내용 삭제
        for widget in self.stats_container.winfo_children():
            widget.destroy()

        try:
            stats = self.db.get_statistics()
        except Exception:
            ttk.Label(self.stats_container, text="통계를 불러올 수 없습니다.",
                      font=("맑은 고딕", 12)).pack(pady=20)
            return

        if stats["total"] == 0:
            ttk.Label(self.stats_container,
                      text="등록된 대상자가 없습니다.\n대상자를 추가하거나 엑셀 파일을 불러와주세요.",
                      font=("맑은 고딕", 12), foreground="#888888").pack(pady=30)
            return

        # 전체 현황 카드
        total_frame = ttk.LabelFrame(self.stats_container, text="📊 전체 현황", padding=10)
        total_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(total_frame, text=f"전체 대상자: {stats['total']}명",
                  font=("맑은 고딕", 16, "bold")).pack(anchor=tk.W)

        # 2열 레이아웃
        row_frame = ttk.Frame(self.stats_container)
        row_frame.pack(fill=tk.X, pady=5)

        # 담당자별 현황
        left = ttk.LabelFrame(row_frame, text="👤 담당자별 대상자 현황", padding=10)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self._create_bar_chart(left, stats["by_manager"], self.MAIN_COLOR, stats["total"])

        # 서비스별 분포
        right = ttk.LabelFrame(row_frame, text="📋 서비스별 분포", padding=10)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self._create_bar_chart(right, stats["by_service"], "#5B9BD5", stats["total"])

        # 2열 레이아웃 (하단)
        row_frame2 = ttk.Frame(self.stats_container)
        row_frame2.pack(fill=tk.X, pady=5)

        # 돌봄등급별 현황
        left2 = ttk.LabelFrame(row_frame2, text="🏥 돌봄등급별 현황", padding=10)
        left2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self._create_bar_chart(left2, stats["by_grade"], "#70AD47", stats["total"])

        # 1인망 연결망 현황
        right2 = ttk.LabelFrame(row_frame2, text="🔗 1인망 연결망 현황", padding=10)
        right2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self._create_network_stats(right2, stats["network"], stats.get("no_network_list", []))

        # 상태별 현황
        status_frame = ttk.LabelFrame(self.stats_container, text="📌 상태별 현황", padding=10)
        status_frame.pack(fill=tk.X, pady=5)
        self._create_bar_chart(status_frame, stats["by_status"], "#ED7D31", stats["total"])

    def _create_bar_chart(self, parent: tk.Widget, data: List[Tuple[str, int]],
                          color: str, total: int) -> None:
        """테이블 + 막대 차트 생성"""
        if not data:
            ttk.Label(parent, text="데이터 없음", foreground="#888888").pack()
            return

        for name, count in data:
            row = ttk.Frame(parent)
            row.pack(fill=tk.X, pady=2)

            # 이름
            ttk.Label(row, text=name, width=15, anchor=tk.W,
                      font=("맑은 고딕", 10)).pack(side=tk.LEFT)

            # 막대
            bar_frame = ttk.Frame(row)
            bar_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))

            ratio = count / total if total > 0 else 0
            bar = tk.Canvas(bar_frame, height=20, highlightthickness=0, bg="#E0E0E0")
            bar.pack(fill=tk.X)
            bar.update_idletasks()
            width = bar.winfo_width()
            if width > 1:
                bar.create_rectangle(0, 0, int(width * ratio), 20, fill=color, outline="")

            # 수치
            pct = f"{ratio * 100:.1f}%" if total > 0 else "0%"
            ttk.Label(row, text=f"{count}명 ({pct})", width=12, anchor=tk.E,
                      font=("맑은 고딕", 9)).pack(side=tk.RIGHT)

        # 막대 크기를 위해 지연 렌더링
        parent.after(100, lambda: self._redraw_bars(parent, data, color, total))

    def _redraw_bars(self, parent: tk.Widget, data: List[Tuple[str, int]],
                     color: str, total: int) -> None:
        """막대 다시 그리기 (크기 확정 후)"""
        for row in parent.winfo_children():
            if isinstance(row, ttk.Frame):
                for child in row.winfo_children():
                    if isinstance(child, ttk.Frame):
                        for canvas in child.winfo_children():
                            if isinstance(canvas, tk.Canvas):
                                canvas.delete("all")
                                width = canvas.winfo_width()
                                # 해당 항목 찾기
                                row_idx = list(parent.winfo_children()).index(row)
                                if row_idx < len(data):
                                    _, count = data[row_idx]
                                    ratio = count / total if total > 0 else 0
                                    canvas.create_rectangle(
                                        0, 0, int(width * ratio), 20,
                                        fill=color, outline=""
                                    )

    def _create_network_stats(self, parent: tk.Widget, network: Dict[str, int],
                              no_network_list: List[Tuple]) -> None:
        """연결망 현황 표시"""
        # 연결망 수별 현황
        items = [
            (f"연결망 0명", network.get("없음", 0), self.RED, "⚠️"),
            (f"연결망 1명", network.get("1명", 0), self.ORANGE, ""),
            (f"연결망 2명 이상", network.get("2명이상", 0), self.GREEN, "✅"),
        ]

        for label, count, color, icon in items:
            row = ttk.Frame(parent)
            row.pack(fill=tk.X, pady=3)
            text = f"{icon} {label}: {count}명" if icon else f"  {label}: {count}명"
            lbl = ttk.Label(row, text=text, font=("맑은 고딕", 11))
            lbl.pack(side=tk.LEFT)

        # 연결망 없는 대상자 목록
        if no_network_list:
            ttk.Separator(parent).pack(fill=tk.X, pady=5)
            ttk.Label(parent, text="⚠️ 연결망 없는 대상자:",
                      font=("맑은 고딕", 10, "bold"), foreground=self.RED).pack(anchor=tk.W)
            for b_id, name, manager in no_network_list:
                ttk.Label(parent, text=f"  • {name} (담당: {manager or '미지정'})",
                          font=("맑은 고딕", 9), foreground=self.RED).pack(anchor=tk.W)
