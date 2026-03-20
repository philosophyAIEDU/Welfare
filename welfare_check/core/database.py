"""
데이터베이스 모듈 - SQLite DB 초기화 및 CRUD 쿼리
모든 데이터는 로컬 SQLite 파일에 저장됨 (100% 오프라인)
"""

import sqlite3
import os
import shutil
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime


class Database:
    """SQLite 데이터베이스 관리 클래스"""

    def __init__(self, db_path: str = "welfare_data.db"):
        """
        데이터베이스 초기화

        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_path = db_path
        self._backup_db()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def _backup_db(self) -> None:
        """프로그램 시작 시 DB 자동 백업"""
        if os.path.exists(self.db_path):
            backup_path = self.db_path.replace(".db", "_backup.db")
            try:
                shutil.copy2(self.db_path, backup_path)
            except Exception:
                pass  # 백업 실패 시 무시하고 계속 진행

    def _create_tables(self) -> None:
        """테이블 자동 생성"""
        cursor = self.conn.cursor()

        # 대상자 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS beneficiaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                address TEXT,
                birth_date TEXT,
                gender TEXT,
                manager TEXT,
                service_type TEXT,
                grade TEXT,
                note TEXT,
                status TEXT DEFAULT '활성',
                registered_date TEXT,
                updated_date TEXT
            )
        """)

        # 1인망 연결망 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS networks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                beneficiary_id INTEGER NOT NULL,
                contact_name TEXT NOT NULL,
                relationship TEXT,
                phone TEXT,
                role TEXT,
                visit_cycle TEXT,
                note TEXT,
                FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id)
                    ON DELETE CASCADE
            )
        """)

        # 안부 확인 이력 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS check_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                beneficiary_id INTEGER NOT NULL,
                check_date TEXT,
                check_type TEXT,
                result TEXT,
                checked_by TEXT,
                memo TEXT,
                FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id)
                    ON DELETE CASCADE
            )
        """)

        self.conn.commit()

    # ==================== 대상자 CRUD ====================

    def add_beneficiary(self, data: Dict[str, Any]) -> int:
        """
        대상자 추가

        Args:
            data: 대상자 정보 딕셔너리

        Returns:
            새로 생성된 대상자 ID
        """
        now = datetime.now().strftime("%Y-%m-%d")
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO beneficiaries
            (name, phone, address, birth_date, gender, manager,
             service_type, grade, note, status, registered_date, updated_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("name", ""),
            data.get("phone", ""),
            data.get("address", ""),
            data.get("birth_date", ""),
            data.get("gender", ""),
            data.get("manager", ""),
            data.get("service_type", ""),
            data.get("grade", ""),
            data.get("note", ""),
            data.get("status", "활성"),
            data.get("registered_date", now),
            now
        ))
        self.conn.commit()
        return cursor.lastrowid

    def update_beneficiary(self, beneficiary_id: int, data: Dict[str, Any]) -> None:
        """대상자 정보 수정"""
        now = datetime.now().strftime("%Y-%m-%d")
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE beneficiaries SET
                name=?, phone=?, address=?, birth_date=?, gender=?,
                manager=?, service_type=?, grade=?, note=?, status=?,
                updated_date=?
            WHERE id=?
        """, (
            data.get("name", ""),
            data.get("phone", ""),
            data.get("address", ""),
            data.get("birth_date", ""),
            data.get("gender", ""),
            data.get("manager", ""),
            data.get("service_type", ""),
            data.get("grade", ""),
            data.get("note", ""),
            data.get("status", "활성"),
            now,
            beneficiary_id
        ))
        self.conn.commit()

    def delete_beneficiary(self, beneficiary_id: int) -> None:
        """대상자 소프트 삭제 (상태를 '삭제됨'으로 변경)"""
        now = datetime.now().strftime("%Y-%m-%d")
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE beneficiaries SET status='삭제됨', updated_date=? WHERE id=?
        """, (now, beneficiary_id))
        self.conn.commit()

    def get_all_beneficiaries(self, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """
        전체 대상자 조회

        Args:
            include_deleted: 삭제된 대상자 포함 여부

        Returns:
            대상자 목록
        """
        cursor = self.conn.cursor()
        if include_deleted:
            cursor.execute("SELECT * FROM beneficiaries ORDER BY id")
        else:
            cursor.execute(
                "SELECT * FROM beneficiaries WHERE status != '삭제됨' ORDER BY id"
            )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_beneficiary(self, beneficiary_id: int) -> Optional[Dict[str, Any]]:
        """대상자 1명 조회"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM beneficiaries WHERE id=?", (beneficiary_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_managers(self) -> List[str]:
        """담당자 목록 조회 (고유값)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT manager FROM beneficiaries
            WHERE status != '삭제됨' AND manager != '' AND manager IS NOT NULL
            ORDER BY manager
        """)
        return [row[0] for row in cursor.fetchall()]

    def get_beneficiaries_by_manager(self, manager: str) -> List[Dict[str, Any]]:
        """담당자별 대상자 조회"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM beneficiaries WHERE manager=? AND status != '삭제됨' ORDER BY id",
            (manager,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def check_duplicate_phone(self, phone: str, exclude_id: Optional[int] = None) -> bool:
        """전화번호 중복 확인"""
        cursor = self.conn.cursor()
        if exclude_id:
            cursor.execute(
                "SELECT COUNT(*) FROM beneficiaries WHERE phone=? AND id!=? AND status!='삭제됨'",
                (phone, exclude_id)
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM beneficiaries WHERE phone=? AND status!='삭제됨'",
                (phone,)
            )
        return cursor.fetchone()[0] > 0

    def bulk_insert_beneficiaries(self, data_list: List[Dict[str, Any]]) -> int:
        """대상자 일괄 추가 (엑셀 불러오기용)"""
        now = datetime.now().strftime("%Y-%m-%d")
        cursor = self.conn.cursor()
        count = 0
        for data in data_list:
            cursor.execute("""
                INSERT INTO beneficiaries
                (name, phone, address, birth_date, gender, manager,
                 service_type, grade, note, status, registered_date, updated_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("name", ""),
                data.get("phone", ""),
                data.get("address", ""),
                data.get("birth_date", ""),
                data.get("gender", ""),
                data.get("manager", ""),
                data.get("service_type", ""),
                data.get("grade", ""),
                data.get("note", ""),
                data.get("status", "활성"),
                data.get("registered_date", now),
                now
            ))
            count += 1
        self.conn.commit()
        return count

    def clear_all_beneficiaries(self) -> None:
        """전체 대상자 삭제 (교체 모드용)"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM networks")
        cursor.execute("DELETE FROM check_logs")
        cursor.execute("DELETE FROM beneficiaries")
        self.conn.commit()

    # ==================== 1인망 연결망 CRUD ====================

    def add_network(self, data: Dict[str, Any]) -> int:
        """연결망 추가"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO networks
            (beneficiary_id, contact_name, relationship, phone, role, visit_cycle, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("beneficiary_id"),
            data.get("contact_name", ""),
            data.get("relationship", ""),
            data.get("phone", ""),
            data.get("role", ""),
            data.get("visit_cycle", ""),
            data.get("note", "")
        ))
        self.conn.commit()
        return cursor.lastrowid

    def update_network(self, network_id: int, data: Dict[str, Any]) -> None:
        """연결망 수정"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE networks SET
                contact_name=?, relationship=?, phone=?, role=?, visit_cycle=?, note=?
            WHERE id=?
        """, (
            data.get("contact_name", ""),
            data.get("relationship", ""),
            data.get("phone", ""),
            data.get("role", ""),
            data.get("visit_cycle", ""),
            data.get("note", ""),
            network_id
        ))
        self.conn.commit()

    def delete_network(self, network_id: int) -> None:
        """연결망 삭제 (실제 삭제)"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM networks WHERE id=?", (network_id,))
        self.conn.commit()

    def get_networks_by_beneficiary(self, beneficiary_id: int) -> List[Dict[str, Any]]:
        """대상자의 연결망 조회"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM networks WHERE beneficiary_id=? ORDER BY id",
            (beneficiary_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_network(self, network_id: int) -> Optional[Dict[str, Any]]:
        """연결망 1건 조회"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM networks WHERE id=?", (network_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_network_count_by_beneficiary(self, beneficiary_id: int) -> int:
        """대상자의 연결망 수 조회"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM networks WHERE beneficiary_id=?",
            (beneficiary_id,)
        )
        return cursor.fetchone()[0]

    def get_all_network_counts(self) -> Dict[int, int]:
        """전체 대상자의 연결망 수 조회"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT b.id, COUNT(n.id) as cnt
            FROM beneficiaries b
            LEFT JOIN networks n ON b.id = n.beneficiary_id
            WHERE b.status != '삭제됨'
            GROUP BY b.id
        """)
        return {row[0]: row[1] for row in cursor.fetchall()}

    # ==================== 안부 확인 이력 CRUD ====================

    def add_check_log(self, data: Dict[str, Any]) -> int:
        """안부 확인 이력 추가"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO check_logs
            (beneficiary_id, check_date, check_type, result, checked_by, memo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.get("beneficiary_id"),
            data.get("check_date", datetime.now().strftime("%Y-%m-%d")),
            data.get("check_type", ""),
            data.get("result", ""),
            data.get("checked_by", ""),
            data.get("memo", "")
        ))
        self.conn.commit()
        return cursor.lastrowid

    def update_check_log(self, log_id: int, data: Dict[str, Any]) -> None:
        """안부 확인 이력 수정"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE check_logs SET
                check_date=?, check_type=?, result=?, checked_by=?, memo=?
            WHERE id=?
        """, (
            data.get("check_date", ""),
            data.get("check_type", ""),
            data.get("result", ""),
            data.get("checked_by", ""),
            data.get("memo", ""),
            log_id
        ))
        self.conn.commit()

    def delete_check_log(self, log_id: int) -> None:
        """안부 확인 이력 삭제"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM check_logs WHERE id=?", (log_id,))
        self.conn.commit()

    def get_check_logs(
        self,
        beneficiary_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        result_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        안부 확인 이력 조회

        Args:
            beneficiary_id: 대상자 ID (None이면 전체)
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            result_filter: 결과 필터
        """
        query = """
            SELECT cl.*, b.name as beneficiary_name
            FROM check_logs cl
            JOIN beneficiaries b ON cl.beneficiary_id = b.id
            WHERE 1=1
        """
        params: List[Any] = []

        if beneficiary_id:
            query += " AND cl.beneficiary_id = ?"
            params.append(beneficiary_id)
        if start_date:
            query += " AND cl.check_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND cl.check_date <= ?"
            params.append(end_date)
        if result_filter and result_filter != "전체":
            query += " AND cl.result = ?"
            params.append(result_filter)

        query += " ORDER BY cl.check_date DESC, cl.id DESC"

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_check_log(self, log_id: int) -> Optional[Dict[str, Any]]:
        """안부 확인 이력 1건 조회"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT cl.*, b.name as beneficiary_name
            FROM check_logs cl
            JOIN beneficiaries b ON cl.beneficiary_id = b.id
            WHERE cl.id=?
        """, (log_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # ==================== 통계 ====================

    def get_statistics(self) -> Dict[str, Any]:
        """통계 데이터 조회"""
        cursor = self.conn.cursor()
        stats: Dict[str, Any] = {}

        # 전체 대상자 수
        cursor.execute("SELECT COUNT(*) FROM beneficiaries WHERE status != '삭제됨'")
        stats["total"] = cursor.fetchone()[0]

        # 담당자별 현황
        cursor.execute("""
            SELECT manager, COUNT(*) as cnt
            FROM beneficiaries WHERE status != '삭제됨' AND manager != ''
            GROUP BY manager ORDER BY cnt DESC
        """)
        stats["by_manager"] = [(row[0], row[1]) for row in cursor.fetchall()]

        # 서비스별 분포
        cursor.execute("""
            SELECT service_type, COUNT(*) as cnt
            FROM beneficiaries WHERE status != '삭제됨' AND service_type != ''
            GROUP BY service_type ORDER BY cnt DESC
        """)
        stats["by_service"] = [(row[0], row[1]) for row in cursor.fetchall()]

        # 돌봄등급별 현황
        cursor.execute("""
            SELECT grade, COUNT(*) as cnt
            FROM beneficiaries WHERE status != '삭제됨' AND grade != ''
            GROUP BY grade ORDER BY cnt DESC
        """)
        stats["by_grade"] = [(row[0], row[1]) for row in cursor.fetchall()]

        # 상태별 현황
        cursor.execute("""
            SELECT status, COUNT(*) as cnt
            FROM beneficiaries
            GROUP BY status ORDER BY cnt DESC
        """)
        stats["by_status"] = [(row[0], row[1]) for row in cursor.fetchall()]

        # 연결망 현황
        cursor.execute("""
            SELECT
                SUM(CASE WHEN cnt = 0 THEN 1 ELSE 0 END) as no_network,
                SUM(CASE WHEN cnt = 1 THEN 1 ELSE 0 END) as one_network,
                SUM(CASE WHEN cnt >= 2 THEN 1 ELSE 0 END) as multi_network
            FROM (
                SELECT b.id, COUNT(n.id) as cnt
                FROM beneficiaries b
                LEFT JOIN networks n ON b.id = n.beneficiary_id
                WHERE b.status != '삭제됨'
                GROUP BY b.id
            )
        """)
        row = cursor.fetchone()
        stats["network"] = {
            "없음": row[0] or 0,
            "1명": row[1] or 0,
            "2명이상": row[2] or 0
        }

        # 연결망 없는 대상자 목록
        cursor.execute("""
            SELECT b.id, b.name, b.manager
            FROM beneficiaries b
            LEFT JOIN networks n ON b.id = n.beneficiary_id
            WHERE b.status != '삭제됨'
            GROUP BY b.id
            HAVING COUNT(n.id) = 0
        """)
        stats["no_network_list"] = [(row[0], row[1], row[2]) for row in cursor.fetchall()]

        return stats

    def close(self) -> None:
        """데이터베이스 연결 종료"""
        if self.conn:
            self.conn.close()
