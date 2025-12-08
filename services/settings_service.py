"""
Settings Service for FRAS

This service manages system settings, loading them from the database and providing
cached access throughout the application. Settings are automatically reloaded
when changed through the admin interface.
"""

import sqlite3
import threading
from typing import Dict, Any, Optional


class SettingsService:
    """Service for managing system settings with database persistence and caching"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._settings_cache: Dict[str, Any] = {}
            self._cache_timestamp = 0
            self._cache_ttl = 300  # 5 minutes cache TTL
            self._db_path = "attendance.db"
            self._initialized = True

    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self._db_path)

    def _load_settings_from_db(self) -> Dict[str, Any]:
        """Load all settings from database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT setting_key, setting_value, setting_type,
                           min_value, max_value, step_value, options
                    FROM system_settings
                """)
                rows = cursor.fetchall()

                settings = {}
                for row in rows:
                    key, value, setting_type, min_val, max_val, step_val, options = row

                    # Convert value based on type
                    if setting_type == "boolean":
                        converted_value = value.lower() == "true"
                    elif setting_type == "number":
                        try:
                            converted_value = float(value)
                        except ValueError:
                            converted_value = get_default_value(key) or 0
                    elif setting_type == "select" and options:
                        converted_value = value  # Keep as string for select
                    else:
                        converted_value = value

                    settings[key] = {
                        "value": converted_value,
                        "type": setting_type,
                        "min": min_val,
                        "max": max_val,
                        "step": step_val,
                        "options": options.split(',') if options else None
                    }

                return settings

        except Exception as e:
            print(f"Error loading settings from database: {e}")
            return {}

    def _should_refresh_cache(self) -> bool:
        """Check if cache should be refreshed"""
        import time
        return time.time() - self._cache_timestamp > self._cache_ttl

    def _refresh_cache(self):
        """Refresh the settings cache"""
        import time
        self._settings_cache = self._load_settings_from_db()
        self._cache_timestamp = time.time()

    def get_setting(self, key: str, default=None):
        """Get a setting value by key"""
        if self._should_refresh_cache():
            self._refresh_cache()

        setting = self._settings_cache.get(key)
        if setting:
            return setting["value"]

        # Fall back to default
        if default is not None:
            return default

        # Hardcoded defaults for critical settings
        defaults = {
            "face_recognition_model": "ArcFace",
            "face_detection_model": "opencv",
            "recognition_threshold": 0.6,
            "face_detection_confidence": 0.8,
            "min_face_size_pixels": 50,
            "max_faces_per_image": 1,
            "late_threshold_minutes": 15,
            "absent_threshold_minutes": 30,
            "early_arrival_grace_minutes": 10,
            "attendance_buffer_minutes": 2,
            "recognition_timeout_seconds": 30,
            "max_concurrent_recognitions": 5,
            "enable_face_recognition": True,
            "anti_spoofing_enabled": False,
            "liveness_detection_enabled": False,
            "cache_embeddings_enabled": True,
            "audit_log_enabled": True,
        }

        return defaults.get(key)

    def get_int_setting(self, key: str, default: int = 0) -> int:
        """Get a setting as integer"""
        value = self.get_setting(key)
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default

    def get_float_setting(self, key: str, default: float = 0.0) -> float:
        """Get a setting as float"""
        value = self.get_setting(key)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def get_bool_setting(self, key: str, default: bool = False) -> bool:
        """Get a setting as boolean"""
        value = self.get_setting(key)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() == "true"
        return default

    def get_str_setting(self, key: str, default: str = "") -> str:
        """Get a setting as string"""
        value = self.get_setting(key)
        return str(value) if value is not None else default

    def invalidate_cache(self):
        """Force cache refresh on next access"""
        self._cache_timestamp = 0

    # Convenience methods for commonly used settings
    @property
    def face_recognition_model(self) -> str:
        return self.get_str_setting("face_recognition_model", "ArcFace")

    @property
    def face_detection_model(self) -> str:
        return self.get_str_setting("face_detection_model", "opencv")

    @property
    def recognition_threshold(self) -> float:
        return self.get_float_setting("recognition_threshold", 0.6)

    @property
    def face_detection_confidence(self) -> float:
        return self.get_float_setting("face_detection_confidence", 0.8)

    @property
    def min_face_size_pixels(self) -> int:
        return self.get_int_setting("min_face_size_pixels", 50)

    @property
    def max_faces_per_image(self) -> int:
        return self.get_int_setting("max_faces_per_image", 1)

    @property
    def late_threshold_minutes(self) -> int:
        return self.get_int_setting("late_threshold_minutes", 15)

    @property
    def absent_threshold_minutes(self) -> int:
        return self.get_int_setting("absent_threshold_minutes", 30)

    @property
    def early_arrival_grace_minutes(self) -> int:
        return self.get_int_setting("early_arrival_grace_minutes", 10)

    @property
    def attendance_buffer_minutes(self) -> int:
        return self.get_int_setting("attendance_buffer_minutes", 2)

    @property
    def recognition_timeout_seconds(self) -> int:
        return self.get_int_setting("recognition_timeout_seconds", 30)

    @property
    def max_concurrent_recognitions(self) -> int:
        return self.get_int_setting("max_concurrent_recognitions", 5)

    @property
    def enable_face_recognition(self) -> bool:
        return self.get_bool_setting("enable_face_recognition", True)

    @property
    def anti_spoofing_enabled(self) -> bool:
        return self.get_bool_setting("anti_spoofing_enabled", False)

    @property
    def liveness_detection_enabled(self) -> bool:
        return self.get_bool_setting("liveness_detection_enabled", False)

    @property
    def cache_embeddings_enabled(self) -> bool:
        return self.get_bool_setting("cache_embeddings_enabled", True)

    @property
    def audit_log_enabled(self) -> bool:
        return self.get_bool_setting("audit_log_enabled", True)


# Global instance
settings_service = SettingsService()


def get_settings_service() -> SettingsService:
    """Get the global settings service instance"""
    return settings_service