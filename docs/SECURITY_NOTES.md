# Security Notes

This document lists security rules and follow-up work for FRAS.

## Do Not Commit

Never commit:

- `.env`
- Real JWT secrets
- Real server passwords
- Real database passwords
- SSH credentials
- Production database dumps
- Private keys
- Panel feedback documents containing credentials
- Local backup databases with sensitive data

## Environment Variables

Use `.env.example` as the committed template.

Use `.env` only locally or on the server.

Recommended variables:

```env
FRAS_ENV=development
FRAS_DB_MODE=sqlite
SQLITE_DB_PATH=attendance.db
JWT_SECRET=replace-with-generated-secret
CORS_ORIGINS=http://localhost:4200,http://localhost:8080
```

## Credential Rotation

If any real password or server credential was shared in a document, chat, screenshot, or commit, rotate it immediately.

Rotate:

- Hosting password.
- SSH password.
- Database password.
- JWT secret.
- Any admin demo credentials if used outside local demo.

## Password Handling Follow-Up

The password reset and authentication flow should be reviewed.

Required future hardening:

1. Remove plaintext password fallback behavior.
2. Remove password hashes from debug logs.
3. Never print reset tokens in production logs.
4. Require strong `JWT_SECRET` from environment.
5. Add token expiry and one-time token invalidation for reset links.
6. Add rate limiting to login and password reset endpoints.
7. Add audit logs for sensitive auth actions.

## Database Backup Safety

The demo reset script creates backups. Do not commit backup files.

Recommended `.gitignore` patterns:

```gitignore
backups/
*.db.backup
*.sqlite.backup
*.dump
```

## Deployment Safety

Before deployment:

```bash
python scripts/check_deployment_config.py
python scripts/project_health_check.py
```

Then manually confirm:

- `.env` exists on the server.
- Real secrets are not inside docs.
- Database file has the correct permissions.
- Admin demo password is changed if exposed publicly.
