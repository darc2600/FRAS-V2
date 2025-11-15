import os
from typing import Optional
from pydantic import BaseModel

class Settings(BaseModel):
    # Database
    database_url: str = "sqlite:///attendance.db"
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True

    # CORS
    cors_origins: list = ["http://localhost:4200", "http://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]

    # File Upload
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    allowed_image_types: list = ["image/jpeg", "image/jpg", "image/png"]
    dataset_path: str = "dataset"

    # Face Recognition
    face_recognition_model: str = "ArcFace"
    face_detection_threshold: float = 0.8

    # AWS S3 (optional)
    s3_bucket: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: Optional[str] = None

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()