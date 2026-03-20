"""
설정 관리 모듈 - config.json 읽기/쓰기
"""

import json
import os
from typing import Any, Dict, Optional


DEFAULT_CONFIG: Dict[str, Any] = {
    "last_file_path": "",
    "column_mapping": {},
    "window_geometry": "1200x800+100+100",
    "sash_position": 250,
    "last_tab": 0,
    "db_path": "welfare_data.db"
}


class Config:
    """설정 파일 관리 클래스"""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """설정 파일 읽기"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.data = DEFAULT_CONFIG.copy()
        else:
            self.data = DEFAULT_CONFIG.copy()
            self.save()

    def save(self) -> None:
        """설정 파일 저장"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except IOError:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        """설정값 읽기"""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """설정값 쓰기"""
        self.data[key] = value
        self.save()

    def get_column_mapping(self) -> Dict[str, str]:
        """열 매핑 설정 가져오기"""
        return self.data.get("column_mapping", {})

    def set_column_mapping(self, mapping: Dict[str, str]) -> None:
        """열 매핑 설정 저장"""
        self.data["column_mapping"] = mapping
        self.save()
