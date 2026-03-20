#!/bin/bash
echo "복지대상자 안부 확인 관리 프로그램 빌드 시작..."
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile --windowed \
    --name "복지대상자_안부확인" \
    --add-data "config.json:." \
    --hidden-import "babel.numbers" \
    main.py
echo "빌드 완료! dist 폴더를 확인하세요."
