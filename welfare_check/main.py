#!/usr/bin/env python3
"""
복지대상자 안부 확인 관리 프로그램
메인 실행 파일 (엔트리포인트)

100% 오프라인으로 동작하며, 모든 데이터는 로컬 SQLite DB에 저장됩니다.
"""

import sys
import os

# PyInstaller 빌드 시 경로 설정
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow


def main():
    """프로그램 메인 함수"""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
