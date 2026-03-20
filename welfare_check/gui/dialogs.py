"""
다이얼로그 모듈 - 입력 폼, 열 매핑 등 다이얼로그
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from ..core.data_loader import FIELD_NAMES, format_phone


# 드롭다운 기본 옵션값
SERVICE_TYPES = ["AI 안부전화", "카카오톡 안부확인", "방문 돌봄", "SMS 안부확인", "무선호출기", "기타"]
GRADES = ["중점돌봄", "일반돌봄", "긴급돌봄", "예방돌봄", "기타"]
STATUSES = ["활성", "중단", "사망", "전출", "시설입소", "기타"]
GENDERS = ["남", "여"]
RELATIONSHIPS = [
    "배우자", "자녀", "딸", "아들", "형제", "손자녀", "기타가족",
    "이웃", "통·반장", "자원봉사자", "복지사", "기타"
]
ROLES = ["1차 연락", "2차 연락", "긴급 연락", "정기 방문", "수시 확인"]
VISIT_CYCLES = ["매일", "주 3회", "주 2회", "주 1회", "격주", "월 2회", "월 1회"]
CHECK_TYPES = ["전화", "카카오톡", "방문", "SMS", "기타"]
CHECK_RESULTS = ["확인완료", "미응답", "부재중", "음성사서함", "기타"]

# 색상 테마
MAIN_COLOR = "#2E5090"
SUB_COLOR = "#E3EBF6"


class BeneficiaryDialog:
    """대상자 추가/수정 다이얼로그"""

    def __init__(
        self,
        parent: tk.Widget,
        title: str = "대상자 정보 입력",
        data: Optional[Dict[str, Any]] = None,
        managers: Optional[List[str]] = None,
        on_save: Optional[Callable] = None,
        check_duplicate_phone: Optional[Callable] = None
    ):
        self.parent = parent
        self.data = data or {}
        self.on_save = on_save
        self.check_duplicate_phone = check_duplicate_phone
        self.result: Optional[Dict[str, Any]] = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("450x550")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.managers = managers or []
        self._build_ui()
        self.dialog.wait_window()

    def _build_ui(self) -> None:
        """UI 구성"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 제목
        title_label = ttk.Label(main_frame, text="대상자 정보 입력",
                                font=("맑은 고딕", 14, "bold"))
        title_label.pack(pady=(0, 15))

        # 입력 필드 프레임
        fields_frame = ttk.Frame(main_frame)
        fields_frame.pack(fill=tk.BOTH, expand=True)

        row = 0

        # 이름 (필수)
        ttk.Label(fields_frame, text="이름 *:", font=("맑은 고딕", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=3)
        self.name_var = tk.StringVar(value=self.data.get("name", ""))
        ttk.Entry(fields_frame, textvariable=self.name_var, width=30).grid(
            row=row, column=1, sticky=tk.W, padx=(10, 0), pady=3)

        row += 1
        # 전화번호 (필수)
        ttk.Label(fields_frame, text="전화번호 *:", font=("맑은 고딕", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=3)
        self.phone_var = tk.StringVar(value=self.data.get("phone", ""))
        ttk.Entry(fields_frame, textvariable=self.phone_var, width=30).grid(
            row=row, column=1, sticky=tk.W, padx=(10, 0), pady=3)

        row += 1
        # 주소
        ttk.Label(fields_frame, text="주소:", font=("맑은 고딕", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=3)
        self.address_var = tk.StringVar(value=self.data.get("address", ""))
        ttk.Entry(fields_frame, textvariable=self.address_var, width=30).grid(
            row=row, column=1, sticky=tk.W, padx=(10, 0), pady=3)

        row += 1
        # 생년월일
        ttk.Label(fields_frame, text="생년월일:", font=("맑은 고딕", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=3)
        self.birth_var = tk.StringVar(value=self.data.get("birth_date", ""))
        birth_entry = ttk.Entry(fields_frame, textvariable=self.birth_var, width=30)
        birth_entry.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=3)

        row += 1
        # 성별
        ttk.Label(fields_frame, text="성별:", font=("맑은 고딕", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=3)
        self.gender_var = tk.StringVar(value=self.data.get("gender", ""))
        gender_frame = ttk.Frame(fields_frame)
        gender_frame.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        for g in GENDERS:
            ttk.Radiobutton(gender_frame, text=g, variable=self.gender_var, value=g).pack(
                side=tk.LEFT, padx=(0, 10))

        row += 1
        # 담당자
        ttk.Label(fields_frame, text="담당자:", font=("맑은 고딕", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=3)
        self.manager_var = tk.StringVar(value=self.data.get("manager", ""))
        manager_combo = ttk.Combobox(fields_frame, textvariable=self.manager_var,
                                     values=self.managers, width=27)
        manager_combo.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=3)

        row += 1
        # 서비스
        ttk.Label(fields_frame, text="서비스:", font=("맑은 고딕", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=3)
        self.service_var = tk.StringVar(value=self.data.get("service_type", ""))
        ttk.Combobox(fields_frame, textvariable=self.service_var,
                     values=SERVICE_TYPES, width=27).grid(
            row=row, column=1, sticky=tk.W, padx=(10, 0), pady=3)

        row += 1
        # 돌봄등급
        ttk.Label(fields_frame, text="돌봄등급:", font=("맑은 고딕", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=3)
        self.grade_var = tk.StringVar(value=self.data.get("grade", ""))
        ttk.Combobox(fields_frame, textvariable=self.grade_var,
                     values=GRADES, width=27).grid(
            row=row, column=1, sticky=tk.W, padx=(10, 0), pady=3)

        row += 1
        # 상태
        ttk.Label(fields_frame, text="상태:", font=("맑은 고딕", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=3)
        self.status_var = tk.StringVar(value=self.data.get("status", "활성"))
        ttk.Combobox(fields_frame, textvariable=self.status_var,
                     values=STATUSES, width=27).grid(
            row=row, column=1, sticky=tk.W, padx=(10, 0), pady=3)

        row += 1
        # 비고
        ttk.Label(fields_frame, text="비고:", font=("맑은 고딕", 10)).grid(
            row=row, column=0, sticky=tk.NW, pady=3)
        self.note_text = tk.Text(fields_frame, width=30, height=3, font=("맑은 고딕", 10))
        self.note_text.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        self.note_text.insert("1.0", self.data.get("note", ""))

        # 버튼
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=(15, 0))

        save_btn = ttk.Button(btn_frame, text="저장", command=self._on_save)
        save_btn.pack(side=tk.LEFT, padx=10)

        cancel_btn = ttk.Button(btn_frame, text="취소", command=self.dialog.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=10)

        # Enter 키로 저장
        self.dialog.bind("<Return>", lambda e: self._on_save())
        self.dialog.bind("<Escape>", lambda e: self.dialog.destroy())

    def _on_save(self) -> None:
        """저장 버튼 클릭"""
        name = self.name_var.get().strip()
        phone = format_phone(self.phone_var.get().strip())

        # 필수 필드 검증
        if not name:
            messagebox.showwarning("입력 오류", "이름을 입력해주세요.", parent=self.dialog)
            return

        # 전화번호 중복 확인
        if phone and self.check_duplicate_phone:
            exclude_id = self.data.get("id")
            if self.check_duplicate_phone(phone, exclude_id):
                if not messagebox.askyesno(
                    "중복 전화번호",
                    f"전화번호 {phone}이(가) 이미 등록되어 있습니다.\n그래도 저장하시겠습니까?",
                    parent=self.dialog
                ):
                    return

        self.result = {
            "name": name,
            "phone": phone,
            "address": self.address_var.get().strip(),
            "birth_date": self.birth_var.get().strip(),
            "gender": self.gender_var.get().strip(),
            "manager": self.manager_var.get().strip(),
            "service_type": self.service_var.get().strip(),
            "grade": self.grade_var.get().strip(),
            "status": self.status_var.get().strip(),
            "note": self.note_text.get("1.0", tk.END).strip(),
        }

        if self.on_save:
            self.on_save(self.result)

        self.dialog.destroy()


class NetworkDialog:
    """1인망 연결망 추가/수정 다이얼로그"""

    def __init__(
        self,
        parent: tk.Widget,
        title: str = "연결망 정보 입력",
        data: Optional[Dict[str, Any]] = None,
        beneficiary_name: str = "",
        on_save: Optional[Callable] = None
    ):
        self.parent = parent
        self.data = data or {}
        self.on_save = on_save
        self.result: Optional[Dict[str, Any]] = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.beneficiary_name = beneficiary_name
        self._build_ui()
        self.dialog.wait_window()

    def _build_ui(self) -> None:
        """UI 구성"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 제목
        if self.beneficiary_name:
            ttk.Label(main_frame, text=f"[{self.beneficiary_name}] 연결망 정보",
                      font=("맑은 고딕", 12, "bold")).pack(pady=(0, 15))

        fields_frame = ttk.Frame(main_frame)
        fields_frame.pack(fill=tk.BOTH, expand=True)

        row = 0

        # 이름
        ttk.Label(fields_frame, text="이름 *:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar(value=self.data.get("contact_name", ""))
        ttk.Entry(fields_frame, textvariable=self.name_var, width=25).grid(
            row=row, column=1, padx=(10, 0), pady=5)

        row += 1
        # 관계
        ttk.Label(fields_frame, text="관계:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.rel_var = tk.StringVar(value=self.data.get("relationship", ""))
        ttk.Combobox(fields_frame, textvariable=self.rel_var,
                     values=RELATIONSHIPS, width=22).grid(
            row=row, column=1, padx=(10, 0), pady=5)

        row += 1
        # 연락처
        ttk.Label(fields_frame, text="연락처:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.phone_var = tk.StringVar(value=self.data.get("phone", ""))
        ttk.Entry(fields_frame, textvariable=self.phone_var, width=25).grid(
            row=row, column=1, padx=(10, 0), pady=5)

        row += 1
        # 역할
        ttk.Label(fields_frame, text="역할:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.role_var = tk.StringVar(value=self.data.get("role", ""))
        ttk.Combobox(fields_frame, textvariable=self.role_var,
                     values=ROLES, width=22).grid(
            row=row, column=1, padx=(10, 0), pady=5)

        row += 1
        # 방문주기
        ttk.Label(fields_frame, text="방문/연락 주기:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.cycle_var = tk.StringVar(value=self.data.get("visit_cycle", ""))
        ttk.Combobox(fields_frame, textvariable=self.cycle_var,
                     values=VISIT_CYCLES, width=22).grid(
            row=row, column=1, padx=(10, 0), pady=5)

        row += 1
        # 비고
        ttk.Label(fields_frame, text="비고:").grid(row=row, column=0, sticky=tk.NW, pady=5)
        self.note_text = tk.Text(fields_frame, width=25, height=3, font=("맑은 고딕", 10))
        self.note_text.grid(row=row, column=1, padx=(10, 0), pady=5)
        self.note_text.insert("1.0", self.data.get("note", ""))

        # 버튼
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=(15, 0))
        ttk.Button(btn_frame, text="저장", command=self._on_save).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="취소", command=self.dialog.destroy).pack(side=tk.LEFT, padx=10)

        self.dialog.bind("<Return>", lambda e: self._on_save())
        self.dialog.bind("<Escape>", lambda e: self.dialog.destroy())

    def _on_save(self) -> None:
        """저장"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("입력 오류", "이름을 입력해주세요.", parent=self.dialog)
            return

        self.result = {
            "contact_name": name,
            "relationship": self.rel_var.get().strip(),
            "phone": format_phone(self.phone_var.get().strip()),
            "role": self.role_var.get().strip(),
            "visit_cycle": self.cycle_var.get().strip(),
            "note": self.note_text.get("1.0", tk.END).strip(),
        }

        if self.on_save:
            self.on_save(self.result)
        self.dialog.destroy()


class CheckLogDialog:
    """안부 확인 이력 추가/수정 다이얼로그"""

    def __init__(
        self,
        parent: tk.Widget,
        title: str = "안부 확인 이력 입력",
        data: Optional[Dict[str, Any]] = None,
        beneficiaries: Optional[List[Dict[str, Any]]] = None,
        selected_beneficiary_id: Optional[int] = None,
        on_save: Optional[Callable] = None
    ):
        self.parent = parent
        self.data = data or {}
        self.on_save = on_save
        self.result: Optional[Dict[str, Any]] = None
        self.beneficiaries = beneficiaries or []
        self.selected_beneficiary_id = selected_beneficiary_id

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("420x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._build_ui()
        self.dialog.wait_window()

    def _build_ui(self) -> None:
        """UI 구성"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="안부 확인 이력 입력",
                  font=("맑은 고딕", 14, "bold")).pack(pady=(0, 15))

        fields_frame = ttk.Frame(main_frame)
        fields_frame.pack(fill=tk.BOTH, expand=True)

        row = 0

        # 대상자 선택
        ttk.Label(fields_frame, text="대상자 *:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.beneficiary_var = tk.StringVar()
        b_names = [f"{b['name']} ({b['id']})" for b in self.beneficiaries]
        b_combo = ttk.Combobox(fields_frame, textvariable=self.beneficiary_var,
                               values=b_names, width=25, state="readonly")
        b_combo.grid(row=row, column=1, padx=(10, 0), pady=5)

        # 기존 데이터 또는 선택된 대상자 설정
        if self.data.get("beneficiary_id"):
            for i, b in enumerate(self.beneficiaries):
                if b["id"] == self.data["beneficiary_id"]:
                    b_combo.current(i)
                    break
        elif self.selected_beneficiary_id:
            for i, b in enumerate(self.beneficiaries):
                if b["id"] == self.selected_beneficiary_id:
                    b_combo.current(i)
                    break

        row += 1
        # 날짜
        ttk.Label(fields_frame, text="날짜:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.date_var = tk.StringVar(
            value=self.data.get("check_date", datetime.now().strftime("%Y-%m-%d")))
        ttk.Entry(fields_frame, textvariable=self.date_var, width=27).grid(
            row=row, column=1, padx=(10, 0), pady=5)

        row += 1
        # 확인방법
        ttk.Label(fields_frame, text="확인방법:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.type_var = tk.StringVar(value=self.data.get("check_type", ""))
        ttk.Combobox(fields_frame, textvariable=self.type_var,
                     values=CHECK_TYPES, width=24).grid(
            row=row, column=1, padx=(10, 0), pady=5)

        row += 1
        # 결과
        ttk.Label(fields_frame, text="결과:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.result_var = tk.StringVar(value=self.data.get("result", ""))
        ttk.Combobox(fields_frame, textvariable=self.result_var,
                     values=CHECK_RESULTS, width=24).grid(
            row=row, column=1, padx=(10, 0), pady=5)

        row += 1
        # 확인자
        ttk.Label(fields_frame, text="확인자:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.checker_var = tk.StringVar(value=self.data.get("checked_by", ""))
        ttk.Entry(fields_frame, textvariable=self.checker_var, width=27).grid(
            row=row, column=1, padx=(10, 0), pady=5)

        row += 1
        # 메모
        ttk.Label(fields_frame, text="메모:").grid(row=row, column=0, sticky=tk.NW, pady=5)
        self.memo_text = tk.Text(fields_frame, width=27, height=3, font=("맑은 고딕", 10))
        self.memo_text.grid(row=row, column=1, padx=(10, 0), pady=5)
        self.memo_text.insert("1.0", self.data.get("memo", ""))

        # 버튼
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=(15, 0))
        ttk.Button(btn_frame, text="저장", command=self._on_save).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="취소", command=self.dialog.destroy).pack(side=tk.LEFT, padx=10)

        self.dialog.bind("<Return>", lambda e: self._on_save())
        self.dialog.bind("<Escape>", lambda e: self.dialog.destroy())

    def _on_save(self) -> None:
        """저장"""
        b_text = self.beneficiary_var.get()
        if not b_text:
            messagebox.showwarning("입력 오류", "대상자를 선택해주세요.", parent=self.dialog)
            return

        # 대상자 ID 추출
        try:
            b_id = int(b_text.split("(")[-1].replace(")", ""))
        except (ValueError, IndexError):
            messagebox.showwarning("입력 오류", "대상자를 다시 선택해주세요.", parent=self.dialog)
            return

        self.result = {
            "beneficiary_id": b_id,
            "check_date": self.date_var.get().strip(),
            "check_type": self.type_var.get().strip(),
            "result": self.result_var.get().strip(),
            "checked_by": self.checker_var.get().strip(),
            "memo": self.memo_text.get("1.0", tk.END).strip(),
        }

        if self.on_save:
            self.on_save(self.result)
        self.dialog.destroy()


class ColumnMappingDialog:
    """엑셀 열 매핑 다이얼로그"""

    def __init__(
        self,
        parent: tk.Widget,
        file_columns: List[str],
        auto_mapping: Dict[str, str],
        on_apply: Optional[Callable] = None
    ):
        self.parent = parent
        self.file_columns = file_columns
        self.on_apply = on_apply
        self.result: Optional[Dict[str, str]] = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("열 매핑 설정")
        self.dialog.geometry("500x500")
        self.dialog.resizable(False, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.mapping_vars: Dict[str, tk.StringVar] = {}
        self._build_ui(auto_mapping)
        self.dialog.wait_window()

    def _build_ui(self, auto_mapping: Dict[str, str]) -> None:
        """UI 구성"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="엑셀 열 매핑 설정",
                  font=("맑은 고딕", 14, "bold")).pack(pady=(0, 5))
        ttk.Label(main_frame,
                  text="엑셀 파일의 각 열이 어떤 필드에 해당하는지 선택하세요.",
                  font=("맑은 고딕", 9)).pack(pady=(0, 15))

        # 매핑 옵션 목록
        field_options = ["(사용 안 함)"] + [f"{v} ({k})" for k, v in FIELD_NAMES.items()]

        # 스크롤 가능 프레임
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>",
                          lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        # 헤더
        ttk.Label(scroll_frame, text="엑셀 열", font=("맑은 고딕", 10, "bold")).grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(scroll_frame, text="→", font=("맑은 고딕", 10)).grid(
            row=0, column=1, padx=5, pady=5)
        ttk.Label(scroll_frame, text="프로그램 필드", font=("맑은 고딕", 10, "bold")).grid(
            row=0, column=2, padx=5, pady=5, sticky=tk.W)

        for idx, col_name in enumerate(self.file_columns):
            row = idx + 1
            ttk.Label(scroll_frame, text=col_name, font=("맑은 고딕", 10)).grid(
                row=row, column=0, padx=5, pady=3, sticky=tk.W)
            ttk.Label(scroll_frame, text="→").grid(row=row, column=1, padx=5, pady=3)

            var = tk.StringVar()
            combo = ttk.Combobox(scroll_frame, textvariable=var,
                                 values=field_options, width=20, state="readonly")
            combo.grid(row=row, column=2, padx=5, pady=3, sticky=tk.W)

            # 자동 매핑 적용
            mapped_field = auto_mapping.get(col_name, "")
            if mapped_field:
                display = FIELD_NAMES.get(mapped_field, "")
                if display:
                    combo.set(f"{display} ({mapped_field})")
                else:
                    combo.set("(사용 안 함)")
            else:
                combo.set("(사용 안 함)")

            self.mapping_vars[col_name] = var

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 버튼
        btn_frame = ttk.Frame(self.dialog, padding=10)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="적용", command=self._on_apply).pack(side=tk.LEFT, padx=10, expand=True)
        ttk.Button(btn_frame, text="취소", command=self.dialog.destroy).pack(side=tk.LEFT, padx=10, expand=True)

    def _on_apply(self) -> None:
        """적용"""
        mapping: Dict[str, str] = {}
        for col_name, var in self.mapping_vars.items():
            val = var.get()
            if val and val != "(사용 안 함)":
                # "이름 (name)" → "name" 추출
                try:
                    field = val.split("(")[-1].replace(")", "").strip()
                    mapping[col_name] = field
                except Exception:
                    pass
            else:
                mapping[col_name] = ""

        self.result = mapping
        if self.on_apply:
            self.on_apply(mapping)
        self.dialog.destroy()


class ExportDialog:
    """내보내기 옵션 다이얼로그"""

    def __init__(self, parent: tk.Widget, on_export: Optional[Callable] = None):
        self.parent = parent
        self.on_export = on_export
        self.result: Optional[str] = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("엑셀 내보내기")
        self.dialog.geometry("350x280")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._build_ui()
        self.dialog.wait_window()

    def _build_ui(self) -> None:
        """UI 구성"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="내보내기 옵션 선택",
                  font=("맑은 고딕", 14, "bold")).pack(pady=(0, 15))

        self.export_var = tk.StringVar(value="current")

        options = [
            ("current", "현재 화면 내보내기 (필터 적용된 데이터)"),
            ("all", "전체 내보내기 (필터 무시)"),
            ("by_manager", "담당자별 시트 분리 내보내기"),
            ("with_network", "1인망 연결망 포함 내보내기"),
        ]

        for value, text in options:
            ttk.Radiobutton(main_frame, text=text, variable=self.export_var,
                            value=value).pack(anchor=tk.W, pady=5)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=(20, 0))
        ttk.Button(btn_frame, text="내보내기", command=self._on_export).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="취소", command=self.dialog.destroy).pack(side=tk.LEFT, padx=10)

    def _on_export(self) -> None:
        """내보내기"""
        self.result = self.export_var.get()
        if self.on_export:
            self.on_export(self.result)
        self.dialog.destroy()
