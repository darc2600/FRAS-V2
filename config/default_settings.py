"""
Default System Settings for FRAS (Facial Recognition Attendance System)

This file contains all default system settings with their values, types, and descriptions.
These defaults are used when the system is first initialized or when settings are reset.

All settings are categorized and include validation ranges where applicable.
"""

# Default system settings with metadata
DEFAULT_SYSTEM_SETTINGS = {
    # Facial Recognition Settings
    "face_recognition_model": {
        "value": "ArcFace",
        "type": "select",
        "category": "facial_recognition",
        "options": ["ArcFace", "Facenet", "VGG-Face", "DeepFace"],
        "description": "Facial recognition model to use for face verification"
    },
    "recognition_threshold": {
        "value": "0.6",
        "type": "number",
        "category": "facial_recognition",
        "min": 0.1,
        "max": 1.0,
        "step": 0.1,
        "description": "Minimum confidence threshold for face recognition (0.1-1.0, higher = stricter)"
    },
    "face_detection_confidence": {
        "value": "0.8",
        "type": "number",
        "category": "facial_recognition",
        "min": 0.1,
        "max": 1.0,
        "step": 0.1,
        "description": "Minimum confidence for face detection (0.1-1.0)"
    },
    "min_face_size_pixels": {
        "value": "50",
        "type": "number",
        "category": "facial_recognition",
        "min": 20,
        "max": 200,
        "description": "Minimum face size in pixels to be considered for recognition"
    },
    "max_faces_per_image": {
        "value": "1",
        "type": "number",
        "category": "facial_recognition",
        "min": 1,
        "max": 5,
        "description": "Maximum number of faces to process per image (prevents multiple recognition)"
    },
    "liveness_detection_enabled": {
        "value": "false",
        "type": "boolean",
        "category": "facial_recognition",
        "description": "Enable real-time liveness detection to ensure person is present"
    },

    # Attendance Logic Settings
    "late_threshold_minutes": {
        "value": "15",
        "type": "number",
        "category": "attendance",
        "min": 1,
        "max": 60,
        "description": "Minutes after class start to be marked as 'Late'"
    },
    "absent_threshold_minutes": {
        "value": "30",
        "type": "number",
        "category": "attendance",
        "min": 1,
        "max": 120,
        "description": "Minutes after class start to be marked as 'Absent'"
    },
    "early_arrival_grace_minutes": {
        "value": "10",
        "type": "number",
        "category": "attendance",
        "min": 0,
        "max": 30,
        "description": "Allow check-in this many minutes before class starts"
    },
    "late_grace_period_minutes": {
        "value": "5",
        "type": "number",
        "category": "attendance",
        "min": 0,
        "max": 15,
        "description": "Additional grace period after late threshold"
    },
    "attendance_buffer_minutes": {
        "value": "2",
        "type": "number",
        "category": "attendance",
        "min": 0,
        "max": 10,
        "description": "Prevent duplicate attendance within this time window"
    },
    "class_end_grace_minutes": {
        "value": "5",
        "type": "number",
        "category": "attendance",
        "min": 0,
        "max": 30,
        "description": "Allow check-in until class end + this grace period"
    },
    "auto_mark_absent_after_minutes": {
        "value": "45",
        "type": "number",
        "category": "attendance",
        "min": 30,
        "max": 120,
        "description": "Auto-mark students as absent if no check-in by this time"
    },

    # Image Processing Settings
    "image_compression_quality": {
        "value": "85",
        "type": "number",
        "category": "image_processing",
        "min": 10,
        "max": 100,
        "description": "JPEG compression quality for stored images (higher = better quality)"
    },
    "max_image_width": {
        "value": "640",
        "type": "number",
        "category": "image_processing",
        "min": 320,
        "max": 1920,
        "description": "Maximum image width for processing and storage"
    },
    "max_image_height": {
        "value": "640",
        "type": "number",
        "category": "image_processing",
        "min": 320,
        "max": 1920,
        "description": "Maximum image height for processing and storage"
    },
    "min_image_resolution": {
        "value": "320",
        "type": "number",
        "category": "image_processing",
        "min": 160,
        "max": 640,
        "description": "Minimum acceptable image resolution (width or height)"
    },
    "face_alignment_enabled": {
        "value": "true",
        "type": "boolean",
        "category": "image_processing",
        "description": "Align faces for better recognition accuracy"
    },
    "image_normalization_enabled": {
        "value": "true",
        "type": "boolean",
        "category": "image_processing",
        "description": "Normalize image lighting and contrast"
    },
    "blur_detection_threshold": {
        "value": "100",
        "type": "number",
        "category": "image_processing",
        "min": 50,
        "max": 500,
        "description": "Threshold for detecting blurry images (higher = stricter)"
    },
    "brightness_min_threshold": {
        "value": "50",
        "type": "number",
        "category": "image_processing",
        "min": 0,
        "max": 255,
        "description": "Minimum acceptable image brightness"
    },
    "brightness_max_threshold": {
        "value": "200",
        "type": "number",
        "category": "image_processing",
        "min": 0,
        "max": 255,
        "description": "Maximum acceptable image brightness"
    },

    # Performance Settings
    "batch_processing_enabled": {
        "value": "true",
        "type": "boolean",
        "category": "performance",
        "description": "Process multiple recognitions in batches for better performance"
    },
    "recognition_timeout_seconds": {
        "value": "30",
        "type": "number",
        "category": "performance",
        "min": 5,
        "max": 120,
        "description": "Maximum time allowed for face recognition attempt"
    },
    "max_concurrent_recognitions": {
        "value": "5",
        "type": "number",
        "category": "performance",
        "min": 1,
        "max": 20,
        "description": "Maximum number of simultaneous recognition processes"
    },
    "cache_embeddings_enabled": {
        "value": "true",
        "type": "boolean",
        "category": "performance",
        "description": "Cache face embeddings in memory for faster recognition"
    },
    "embedding_cache_ttl_hours": {
        "value": "24",
        "type": "number",
        "category": "performance",
        "min": 1,
        "max": 168,
        "description": "How long to keep embeddings cached (hours)"
    },
    "failed_recognition_retry_count": {
        "value": "3",
        "type": "number",
        "category": "performance",
        "min": 0,
        "max": 10,
        "description": "Number of retry attempts for failed recognitions"
    },

    # Security & Privacy Settings
    "face_data_retention_days": {
        "value": "365",
        "type": "number",
        "category": "security",
        "min": 30,
        "max": 2555,
        "description": "Days to retain face images before automatic deletion"
    },
    "gdpr_compliance_enabled": {
        "value": "true",
        "type": "boolean",
        "category": "security",
        "description": "Enable GDPR compliance features and data handling"
    },
    "audit_log_enabled": {
        "value": "true",
        "type": "boolean",
        "category": "security",
        "description": "Log all recognition attempts and system activities"
    },
    "failed_attempt_logging": {
        "value": "true",
        "type": "boolean",
        "category": "security",
        "description": "Log failed recognition attempts for security monitoring"
    },
    "max_failed_attempts_per_hour": {
        "value": "10",
        "type": "number",
        "category": "security",
        "min": 1,
        "max": 100,
        "description": "Maximum failed attempts allowed per hour per user"
    },

    # User Experience Settings
    "real_time_feedback_enabled": {
        "value": "true",
        "type": "boolean",
        "category": "ux",
        "description": "Show recognition results immediately to users"
    },
    "instructor_alerts_enabled": {
        "value": "true",
        "type": "boolean",
        "category": "ux",
        "description": "Send alerts to instructors about attendance issues"
    },
    "attendance_report_frequency": {
        "value": "daily",
        "type": "select",
        "category": "ux",
        "options": ["daily", "weekly", "monthly", "never"],
        "description": "How often to generate automated attendance reports"
    },

    # Hardware Settings
    "camera_resolution_preferred": {
        "value": "720p",
        "type": "select",
        "category": "hardware",
        "options": ["480p", "720p", "1080p", "4k"],
        "description": "Preferred camera resolution for capture"
    },
    "camera_fps_preferred": {
        "value": "30",
        "type": "number",
        "category": "hardware",
        "min": 15,
        "max": 60,
        "description": "Preferred camera frames per second"
    },
    "multiple_camera_support": {
        "value": "true",
        "type": "boolean",
        "category": "hardware",
        "description": "Support multiple cameras for attendance tracking"
    },
    "device_authentication_required": {
        "value": "true",
        "type": "boolean",
        "category": "hardware",
        "description": "Require device authentication for attendance terminals"
    },
    "auto_device_detection": {
        "value": "true",
        "type": "boolean",
        "category": "hardware",
        "description": "Automatically detect and configure connected cameras"
    },

    # System Settings
    "enable_face_recognition": {
        "value": "true",
        "type": "boolean",
        "category": "system",
        "description": "Enable facial recognition features system-wide"
    },
    "session_timeout_minutes": {
        "value": "1440",
        "type": "number",
        "category": "system",
        "min": 30,
        "max": 10080,
        "description": "User session timeout in minutes"
    },
    "backup_frequency_hours": {
        "value": "24",
        "type": "number",
        "category": "system",
        "min": 1,
        "max": 168,
        "description": "How often to perform automatic system backups"
    },
    "max_attendance_retention_days": {
        "value": "365",
        "type": "number",
        "category": "system",
        "min": 30,
        "max": 2555,
        "description": "Maximum days to retain attendance records"
    },
    "sync_interval_minutes": {
        "value": "15",
        "type": "number",
        "category": "system",
        "min": 5,
        "max": 1440,
        "description": "How often to sync data with central server"
    },
    "holiday_attendance_allowed": {
        "value": "false",
        "type": "boolean",
        "category": "system",
        "description": "Allow attendance marking on holidays"
    },
}

# Combine all settings
ALL_DEFAULT_SETTINGS = DEFAULT_SYSTEM_SETTINGS

def get_default_setting(key: str):
    """Get a default setting by key"""
    return ALL_DEFAULT_SETTINGS.get(key)

def get_default_value(key: str):
    """Get just the default value for a setting"""
    setting = get_default_setting(key)
    return setting["value"] if setting else None

def get_settings_by_category(category: str):
    """Get all settings for a specific category"""
    return {k: v for k, v in ALL_DEFAULT_SETTINGS.items() if v.get("category") == category}

def validate_setting_value(key: str, value: str) -> bool:
    """Validate if a value is acceptable for a setting"""
    setting = get_default_setting(key)
    if not setting:
        return False

    setting_type = setting["type"]

    if setting_type == "boolean":
        return value.lower() in ["true", "false"]
    elif setting_type == "number":
        try:
            num_value = float(value)
            min_val = setting.get("min")
            max_val = setting.get("max")
            if min_val is not None and num_value < min_val:
                return False
            if max_val is not None and num_value > max_val:
                return False
            return True
        except ValueError:
            return False
    elif setting_type == "select":
        options = setting.get("options", [])
        return value in options
    else:  # text, config, etc.
        return len(value.strip()) > 0