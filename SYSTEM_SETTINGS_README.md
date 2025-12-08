# FRAS System Settings Documentation

## Overview

The Facial Recognition Attendance System (FRAS) now includes a comprehensive settings management system that allows administrators to configure all aspects of the system's behavior. Settings are stored in the database and take effect immediately when changed.

## Settings Categories

### 🎯 Facial Recognition Settings
Control how faces are detected and recognized:

- **`face_recognition_model`**: Model used for face verification
  - Options: `ArcFace`, `Facenet`, `VGG-Face`, `DeepFace`
  - Default: `ArcFace`

- **`face_detection_model`**: Model used for face detection
  - Options: `opencv`, `mtcnn`, `dlib`, `retinaface`
  - Default: `opencv`

- **`recognition_threshold`**: Minimum confidence for face match (0.1-1.0)
  - Default: `0.6` (higher = stricter matching)

- **`face_detection_confidence`**: Minimum confidence for face detection (0.1-1.0)
  - Default: `0.8`

- **`min_face_size_pixels`**: Minimum face size in pixels
  - Default: `50` (prevents false detections of small faces)

- **`max_faces_per_image`**: Maximum faces to process per image
  - Default: `1` (prevents multiple recognitions)

- **`anti_spoofing_enabled`**: Enable detection of fake faces/photos
  - Default: `false`

- **`liveness_detection_enabled`**: Enable real-time liveness detection
  - Default: `false`

### ⏰ Attendance Logic Settings
Configure attendance marking rules:

- **`late_threshold_minutes`**: Minutes after class start to mark as "Late"
  - Default: `15` minutes

- **`absent_threshold_minutes`**: Minutes after class start to mark as "Absent"
  - Default: `30` minutes

- **`early_arrival_grace_minutes`**: Allow check-in before class starts
  - Default: `10` minutes

- **`late_grace_period_minutes`**: Additional grace after late threshold
  - Default: `5` minutes

- **`attendance_buffer_minutes`**: Prevent duplicate attendance within timeframe
  - Default: `2` minutes

- **`class_end_grace_minutes`**: Allow check-in until class end + grace
  - Default: `5` minutes

- **`auto_mark_absent_after_minutes`**: Auto-mark absent after this time
  - Default: `45` minutes

### 🖼️ Image Processing Settings
Control image quality and processing:

- **`image_compression_quality`**: JPEG quality for stored images (10-100)
  - Default: `85`

- **`max_image_width`**: Maximum image width for processing
  - Default: `640` pixels

- **`max_image_height`**: Maximum image height for processing
  - Default: `640` pixels

- **`face_alignment_enabled`**: Align faces for better recognition
  - Default: `true`

- **`image_normalization_enabled`**: Normalize lighting and contrast
  - Default: `true`

### ⚡ Performance Settings
Optimize system performance:

- **`batch_processing_enabled`**: Process multiple recognitions together
  - Default: `true`

- **`recognition_timeout_seconds`**: Maximum time for recognition
  - Default: `30` seconds

- **`max_concurrent_recognitions`**: Maximum simultaneous processes
  - Default: `5`

- **`cache_embeddings_enabled`**: Cache face embeddings in memory
  - Default: `true`

- **`embedding_cache_ttl_hours`**: Cache duration
  - Default: `24` hours

### 🔒 Security & Privacy Settings
Configure security features:

- **`face_data_retention_days`**: Days to keep face images
  - Default: `365` days

- **`audit_log_enabled`**: Log all recognition attempts
  - Default: `true`

- **`max_failed_attempts_per_hour`**: Rate limiting for failed attempts
  - Default: `10`

### 👥 User Experience Settings
Control user interface and notifications:

- **`real_time_feedback_enabled`**: Show results immediately
  - Default: `true`

- **`notification_email_enabled`**: Send email notifications
  - Default: `true`

- **`instructor_alerts_enabled`**: Alert instructors of issues
  - Default: `true`

### 📷 Hardware Settings
Configure camera and device settings:

- **`camera_resolution_preferred`**: Preferred camera resolution
  - Options: `480p`, `720p`, `1080p`, `4k`
  - Default: `720p`

- **`multiple_camera_support`**: Support multiple cameras
  - Default: `true`

## Technical Implementation

### Settings Storage
- Settings are stored in the `system_settings` table in the database
- Each setting has: key, value, type, category, validation rules
- Changes take effect immediately through cache invalidation

### Settings Service
- `services/settings_service.py` provides cached access to settings
- Automatic cache refresh every 5 minutes
- Type-safe getters for different data types

### Integration Points
- **Recognition Repository**: Uses facial recognition and attendance settings
- **GUI Application**: Uses recognition settings for desktop interface
- **API Endpoints**: Cache invalidation on setting updates

### Default Values
All default values are documented in `config/default_settings.py` with:
- Value ranges and validation rules
- Descriptions for each setting
- Category organization

## Usage Examples

### Changing Recognition Sensitivity
```python
# Make recognition more strict (higher threshold)
settings_service.update_setting("recognition_threshold", "0.8")

# Make recognition more lenient (lower threshold)
settings_service.update_setting("recognition_threshold", "0.4")
```

### Adjusting Attendance Rules
```python
# Extend late threshold to 20 minutes
settings_service.update_setting("late_threshold_minutes", "20")

# Allow check-in 15 minutes early
settings_service.update_setting("early_arrival_grace_minutes", "15")
```

### Performance Tuning
```python
# Increase concurrent recognitions for better performance
settings_service.update_setting("max_concurrent_recognitions", "10")

# Reduce timeout for faster failure detection
settings_service.update_setting("recognition_timeout_seconds", "20")
```

## Administration

Settings can be managed through:
1. **Web Interface**: System Settings page in the admin panel
2. **API**: `PUT /api/admin/system-settings`
3. **Database**: Direct updates to `system_settings` table

All changes are logged and take effect immediately throughout the system.