"""
메인 윈도우 - 탭 관리 및 전체 레이아웃
"""

import tkinter as tk
from tkinter import ttk
import os
import sys
from typing import Dict

from .tab_beneficiary import BeneficiaryTab
from .tab_network import NetworkTab
from .tab_check_log import CheckLogTab
from .tab_statistics import StatisticsTab
from .statusbar import StatusBar
from ..core.database import Database
from ..core.config import Config


class MainWindow:
    """메인 윈도우 클래스"""

    # 색상 테마
    MAIN_COLOR = "#2E5090"
    SUB_COLOR = "#E3EBF6"
    BG_COLOR = "#F5F5F5"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("복지대상자 안부 확인 관리 프로그램")
        self.root.minsize(1000, 700)

        # 실행 파일 경로 기준으로 설정
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # 설정 로드
        config_path = os.path.join(self.base_dir, "config.json")
        self.config = Config(config_path)

        # 데이터베이스 초기화
        db_path = os.path.join(self.base_dir, self.config.get("db_path", "welfare_data.db"))
        self.db = Database(db_path)

        # 창 크기/위치 복원
        geometry = self.config.get("window_geometry", "1200x800+100+100")
        try:
            self.root.geometry(geometry)
        except Exception:
            self.root.geometry("1200x800+100+100")

        self._setup_style()
        self._build_ui()
        self._setup_shortcuts()

        # 마지막 탭 복원
        last_tab = self.config.get("last_tab", 0)
        try:
            self.notebook.select(last_tab)
        except Exception:
            pass

        # 창 닫기 이벤트
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_style(self) -> None:
        """ttk 스타일 설정"""
        style = ttk.Style()

        # 폰트 설정
        default_font = ("맑은 고딕", 10)
        style.configure(".", font=default_font)
        style.configure("TButton", font=default_font, padding=5)
        style.configure("TLabel", font=default_font)
        style.configure("TNotebook.Tab", font=("맑은 고딕", 11), padding=[15, 5])
        style.configure("Heading", font=("맑은 고딕", 10, "bold"))

        # Treeview 스타일
        style.configure("Treeview", font=default_font, rowheight=28)
        style.configure("Treeview.Heading", font=("맑은 고딕", 10, "bold"))

    def _build_ui(self) -> None:
        """UI 구성"""
        # 상태바
        self.statusbar = StatusBar(self.root)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

        # 노트북 (탭)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 탭 1: 대상자 관리
        self.tab_beneficiary = BeneficiaryTab(
            self.notebook, self.db, self.config,
            status_callback=self._update_statusbar
        )
        self.notebook.add(self.tab_beneficiary, text="  대상자 관리  ")

        # 탭 2: 1인망 연결망
        self.tab_network = NetworkTab(self.notebook, self.db)
        self.notebook.add(self.tab_network, text="  1인망 연결망  ")

        # 탭 3: 안부 확인 이력
        self.tab_check_log = CheckLogTab(self.notebook, self.db)
        self.notebook.add(self.tab_check_log, text="  안부 확인 이력  ")

        # 탭 4: 통계
        self.tab_statistics = StatisticsTab(self.notebook, self.db)
        self.notebook.add(self.tab_statistics, text="  통계  ")

        # 탭 전환 이벤트
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _setup_shortcuts(self) -> None:
        """키보드 단축키 설정"""
        self.root.bind("<Control-o>", lambda e: self.tab_beneficiary.import_excel())
        self.root.bind("<Control-O>", lambda e: self.tab_beneficiary.import_excel())
        self.root.bind("<Control-n>", lambda e: self.tab_beneficiary.add_beneficiary())
        self.root.bind("<Control-N>", lambda e: self.tab_beneficiary.add_beneficiary())
        self.root.bind("<Control-f>", lambda e: self._focus_search())
        self.root.bind("<Control-F>", lambda e: self._focus_search())
        self.root.bind("<Control-e>", lambda e: self.tab_beneficiary.export_excel())
        self.root.bind("<Control-E>", lambda e: self.tab_beneficiary.export_excel())
        self.root.bind("<F5>", lambda e: self._refresh_current_tab())
        self.root.bind("<Delete>", lambda e: self._delete_selected())
        self.root.bind("<Escape>", lambda e: self._clear_search())

        # 탭 전환 (Ctrl+1~4)
        for i in range(4):
            self.root.bind(f"<Control-{i+1}>",
                           lambda e, idx=i: self.notebook.select(idx))

    def _focus_search(self) -> None:
        """검색창 포커스"""
        current = self.notebook.index(self.notebook.select())
        if current == 0:
            self.tab_beneficiary.search_entry.focus_set()

    def _refresh_current_tab(self) -> None:
        """현재 탭 새로고침"""
        current = self.notebook.index(self.notebook.select())
        if current == 0:
            self.tab_beneficiary.refresh_data()
        elif current == 1:
            self.tab_network.refresh_beneficiary_list()
        elif current == 2:
            self.tab_check_log.refresh_data()
        elif current == 3:
            self.tab_statistics.refresh_stats()

    def _delete_selected(self) -> None:
        """현재 탭에서 선택 삭제"""
        current = self.notebook.index(self.notebook.select())
        if current == 0:
            self.tab_beneficiary.delete_beneficiary()
        elif current == 1:
            self.tab_network.delete_network()
        elif current == 2:
            self.tab_check_log.delete_log()

    def _clear_search(self) -> None:
        """검색/필터 초기화"""
        current = self.notebook.index(self.notebook.select())
        if current == 0:
            self.tab_beneficiary.clear_filters()

    def _on_tab_changed(self, event) -> None:
        """탭 전환 이벤트"""
        current = self.notebook.index(self.notebook.select())
        self.config.set("last_tab", current)

        # 탭 전환 시 데이터 갱신
        if current == 1:
            self.tab_network.refresh_beneficiary_list()
        elif current == 2:
            self.tab_check_log.refresh_data()
        elif current == 3:
            self.tab_statistics.refresh_stats()

    def _update_statusbar(self, total: int, filtered: int,
                          managers: int = 0, service_stats: Dict = None) -> None:
        """상태바 업데이트 콜백"""
        self.statusbar.update_counts(total, filtered, managers, service_stats)

    def _on_close(self) -> None:
        """프로그램 종료"""
        # 설정 저장
        self.config.set("window_geometry", self.root.geometry())
        self.config.save()

        # DB 닫기
        self.db.close()
        self.root.destroy()

    def run(self) -> None:
        """프로그램 실행"""
        self.root.mainloop()
