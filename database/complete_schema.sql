-- FRAS Database Schema - Complete User Management System
-- This file documents the complete database structure for the Facial Recognition Attendance System

-- ============================================================================
-- USER MANAGEMENT SYSTEM TABLES
-- ============================================================================

-- Users table - Central authentication table
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('instructor', 'it_admin', 'super_admin')),
    reference_id INTEGER NOT NULL, -- References instructor/it_admin/super_admin ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Permissions table - Defines all available permissions
CREATE TABLE IF NOT EXISTS permissions (
    permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    permission_code TEXT UNIQUE NOT NULL,
    permission_name TEXT NOT NULL,
    description TEXT,
    category TEXT
);

-- Role permissions table - Links roles to permissions
CREATE TABLE IF NOT EXISTS role_permissions (
    user_type TEXT NOT NULL,
    permission_id INTEGER NOT NULL REFERENCES permissions(permission_id),
    PRIMARY KEY (user_type, permission_id)
);

-- IT Admins table
CREATE TABLE IF NOT EXISTS it_admins (
    it_admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_number VARCHAR(20) UNIQUE,
    last_name TEXT,
    first_name TEXT,
    email TEXT UNIQUE,
    dept_id INTEGER REFERENCES departments(dept_id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Super Admins table
CREATE TABLE IF NOT EXISTS super_admins (
    super_admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_number VARCHAR(20) UNIQUE,
    last_name TEXT,
    first_name TEXT,
    email TEXT UNIQUE,
    dept_id INTEGER REFERENCES departments(dept_id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- System settings table
CREATE TABLE IF NOT EXISTS system_settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT,
    setting_type TEXT,
    updated_by INTEGER REFERENCES users(user_id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Support ticket system
CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    subject TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT CHECK (category IN ('technical', 'account', 'attendance', 'feature', 'other')),
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    assigned_to INTEGER REFERENCES users(user_id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ticket_replies (
    reply_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL REFERENCES support_tickets(ticket_id),
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    message TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- DEFAULT DATA INSERTION
-- ============================================================================

-- Insert default permissions
INSERT OR IGNORE INTO permissions (permission_code, permission_name, description, category) VALUES
('view_own_schedule', 'View personal schedule', 'View personal schedule', 'schedule'),
('view_attendance_logs', 'View attendance logs', 'View attendance logs', 'attendance'),
('mark_attendance', 'Mark attendance using facial recognition', 'Mark attendance using facial recognition', 'attendance'),
('register_students', 'Register new students', 'Register new students', 'registration'),
('manage_users', 'Create and manage user accounts', 'Create and manage user accounts', 'user_management'),
('manage_rooms_schedule', 'Edit room and schedule configurations', 'Edit room and schedule configurations', 'administration'),
('system_admin', 'Full system administration access', 'Full system administration access', 'administration'),
('view_analytics', 'View system analytics and reports', 'View system analytics and reports', 'analytics'),
('manage_content', 'Manage system content and settings', 'Manage system content and settings', 'content');

-- Insert default role permissions
INSERT OR IGNORE INTO role_permissions (user_type, permission_id) VALUES
-- Instructor permissions
('instructor', (SELECT permission_id FROM permissions WHERE permission_code = 'view_own_schedule')),
('instructor', (SELECT permission_id FROM permissions WHERE permission_code = 'view_attendance_logs')),
('instructor', (SELECT permission_id FROM permissions WHERE permission_code = 'mark_attendance')),
('instructor', (SELECT permission_id FROM permissions WHERE permission_code = 'register_students')),

-- IT Admin permissions
('it_admin', (SELECT permission_id FROM permissions WHERE permission_code = 'view_own_schedule')),
('it_admin', (SELECT permission_id FROM permissions WHERE permission_code = 'view_attendance_logs')),
('it_admin', (SELECT permission_id FROM permissions WHERE permission_code = 'mark_attendance')),
('it_admin', (SELECT permission_id FROM permissions WHERE permission_code = 'register_students')),
('it_admin', (SELECT permission_id FROM permissions WHERE permission_code = 'manage_users')),
('it_admin', (SELECT permission_id FROM permissions WHERE permission_code = 'manage_rooms_schedule')),
('it_admin', (SELECT permission_id FROM permissions WHERE permission_code = 'view_analytics')),

-- Super Admin permissions (all permissions)
('super_admin', (SELECT permission_id FROM permissions WHERE permission_code = 'view_own_schedule')),
('super_admin', (SELECT permission_id FROM permissions WHERE permission_code = 'view_attendance_logs')),
('super_admin', (SELECT permission_id FROM permissions WHERE permission_code = 'mark_attendance')),
('super_admin', (SELECT permission_id FROM permissions WHERE permission_code = 'register_students')),
('super_admin', (SELECT permission_id FROM permissions WHERE permission_code = 'manage_users')),
('super_admin', (SELECT permission_id FROM permissions WHERE permission_code = 'manage_rooms_schedule')),
('super_admin', (SELECT permission_id FROM permissions WHERE permission_code = 'system_admin')),
('super_admin', (SELECT permission_id FROM permissions WHERE permission_code = 'view_analytics')),
('super_admin', (SELECT permission_id FROM permissions WHERE permission_code = 'manage_content'));

-- Insert default system settings
INSERT OR IGNORE INTO system_settings (setting_key, setting_value, setting_type) VALUES
('system_name', 'FRAS - Facial Recognition Attendance System', 'config'),
('version', '1.0.0', 'config'),
('maintenance_mode', 'false', 'config'),
('max_upload_size', '10485760', 'config'), -- 10MB
('session_timeout', '3600', 'config'), -- 1 hour
('face_recognition_threshold', '0.6', 'config'),
('backup_frequency', 'daily', 'config'),
('log_retention_days', '90', 'config'),
('email_notifications', 'true', 'config');

-- ============================================================================
-- LEGACY TABLES (for reference - these are handled by init_database.py)
-- ============================================================================
-- The following tables are created by init_database.py:
-- students, instructors, courses, departments, room_types, attendance_status_types,
-- campuses, buildings, rooms, school_terms, classes, enrollments, attendance_logs, admins