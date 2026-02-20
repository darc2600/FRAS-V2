-- User Types and Permissions Schema Updates for FRAS Thesis
-- Phase 1: User Types System Implementation

-- Add user_type to existing tables
ALTER TABLE students ADD COLUMN user_type TEXT DEFAULT 'regular';
ALTER TABLE instructors ADD COLUMN user_type TEXT DEFAULT 'regular';
ALTER TABLE admins ADD COLUMN user_type TEXT DEFAULT 'super_admin';

-- Add user_type to users table if not exists
ALTER TABLE users ADD COLUMN user_type TEXT DEFAULT 'regular';

-- Create permissions system
CREATE TABLE IF NOT EXISTS permissions (
    permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    permission_name TEXT UNIQUE NOT NULL,
    description TEXT,
    category TEXT
);

CREATE TABLE IF NOT EXISTS role_permissions (
    user_type TEXT NOT NULL,
    permission_id INTEGER REFERENCES permissions(permission_id),
    PRIMARY KEY (user_type, permission_id)
);

-- System settings for content management
CREATE TABLE IF NOT EXISTS system_settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT,
    setting_type TEXT,
    updated_by INTEGER REFERENCES users(user_id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit logging for security
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(user_id),
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id INTEGER,
    details TEXT,
    ip_address TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default permissions
INSERT OR IGNORE INTO permissions (permission_name, description, category) VALUES
('view_own_attendance', 'View personal attendance records', 'attendance'),
('mark_attendance', 'Use facial recognition to mark attendance', 'attendance'),
('manage_users', 'Create, edit, delete user accounts', 'user_management'),
('reset_passwords', 'Reset other users passwords', 'user_management'),
('view_system_logs', 'Access basic system logs', 'monitoring'),
('system_config', 'Modify system settings and configurations', 'administration'),
('view_all_data', 'Access all attendance records and analytics', 'data'),
('manage_admins', 'Create and manage IT Admin accounts', 'administration'),
('content_management', 'Manage themes, logos, and content', 'content'),
('audit_logs', 'View complete system audit logs', 'security'),
('submit_support', 'Submit support tickets', 'support'),
('manage_support', 'View and manage support tickets', 'support');

-- Assign permissions to roles
INSERT OR IGNORE INTO role_permissions (user_type, permission_id) VALUES
-- Regular user permissions
((SELECT permission_id FROM permissions WHERE permission_name = 'view_own_attendance'), 'regular'),
((SELECT permission_id FROM permissions WHERE permission_name = 'mark_attendance'), 'regular'),
((SELECT permission_id FROM permissions WHERE permission_name = 'submit_support'), 'regular'),

-- IT Admin permissions
((SELECT permission_id FROM permissions WHERE permission_name = 'view_own_attendance'), 'it_admin'),
((SELECT permission_id FROM permissions WHERE permission_name = 'mark_attendance'), 'it_admin'),
((SELECT permission_id FROM permissions WHERE permission_name = 'manage_users'), 'it_admin'),
((SELECT permission_id FROM permissions WHERE permission_name = 'reset_passwords'), 'it_admin'),
((SELECT permission_id FROM permissions WHERE permission_name = 'view_system_logs'), 'it_admin'),
((SELECT permission_id FROM permissions WHERE permission_name = 'submit_support'), 'it_admin'),
((SELECT permission_id FROM permissions WHERE permission_name = 'manage_support'), 'it_admin'),

-- Super Admin permissions (all permissions)
((SELECT permission_id FROM permissions WHERE permission_name = 'view_own_attendance'), 'super_admin'),
((SELECT permission_id FROM permissions WHERE permission_name = 'mark_attendance'), 'super_admin'),
((SELECT permission_id FROM permissions WHERE permission_name = 'manage_users'), 'super_admin'),
((SELECT permission_id FROM permissions WHERE permission_name = 'reset_passwords'), 'super_admin'),
((SELECT permission_id FROM permissions WHERE permission_name = 'view_system_logs'), 'super_admin'),
((SELECT permission_id FROM permissions WHERE permission_name = 'system_config'), 'super_admin'),
((SELECT permission_id FROM permissions WHERE permission_name = 'view_all_data'), 'super_admin'),
((SELECT permission_id FROM permissions WHERE permission_name = 'manage_admins'), 'super_admin'),
((SELECT permission_id FROM permissions WHERE permission_name = 'content_management'), 'super_admin'),
((SELECT permission_id FROM permissions WHERE permission_name = 'audit_logs'), 'super_admin'),
((SELECT permission_id FROM permissions WHERE permission_name = 'submit_support'), 'super_admin'),
((SELECT permission_id FROM permissions WHERE permission_name = 'manage_support'), 'super_admin');

-- Insert default system settings
INSERT OR IGNORE INTO system_settings (setting_key, setting_value, setting_type) VALUES
('theme_primary_color', '#007bff', 'theme'),
('theme_secondary_color', '#6c757d', 'theme'),
('system_logo_url', '/assets/logo.png', 'logo'),
('system_name', 'FRAS - Facial Recognition Attendance System', 'config'),
('recognition_threshold', '0.6', 'config'),
('late_threshold_minutes', '15', 'config'),
('absent_threshold_minutes', '30', 'config'),
('welcome_message', 'Welcome to FRAS', 'content'),
('user_guide', 'Please follow the attendance marking procedure.', 'content');