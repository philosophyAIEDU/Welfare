@echo off
chcp 65001 > nul
echo ========================================
echo  복지대상자 안부 확인 관리 프로그램 빌드
echo ========================================
echo.

echo [1/3] 필요 패키지 설치 중...
pip install -r requirements.txt
pip install pyinstaller

echo [2/3] exe 파일 빌드 중...
pyinstaller --onefile --windowed ^
    --name "복지대상자_안부확인" ^
    --add-data "config.json;." ^
    --hidden-import "babel.numbers" ^
    main.py

echo [3/3] 빌드 완료!
echo.
echo dist 폴더에서 "복지대상자_안부확인.exe" 파일을 확인하세요.
echo 이 exe 파일만 복사하면 다른 PC에서도 실행할 수 있습니다.
pause
