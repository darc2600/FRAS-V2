from __future__ import annotations

import os
import posixpath
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import paramiko


HOST = "92.205.61.8"
USER = "frasijbmapua"
REMOTE_DIR = "/home/frasijbmapua/FRAS"
REMOTE_TAR = "/home/frasijbmapua/fras_v2_latest.tar.gz"
LOCAL_ROOT = Path(__file__).resolve().parent


def run_local(command: list[str], cwd: Path = LOCAL_ROOT) -> str:
    result = subprocess.run(command, cwd=cwd, check=True, text=True, capture_output=True)
    return result.stdout


def build_archive() -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="fras_v2_deploy_"))
    archive_path = temp_dir / "fras_v2_latest.tar.gz"
    try:
      tracked = run_local(["git", "-c", f"safe.directory={LOCAL_ROOT.as_posix()}", "ls-files"])
    except subprocess.CalledProcessError as exc:
      print(exc.stdout)
      print(exc.stderr, file=sys.stderr)
      raise

    files = [LOCAL_ROOT / line.strip() for line in tracked.splitlines() if line.strip()]
    with tarfile.open(archive_path, "w:gz") as tar:
        for file_path in files:
            if file_path.is_file():
                tar.add(file_path, arcname=file_path.relative_to(LOCAL_ROOT).as_posix())
    return archive_path


def connect() -> paramiko.SSHClient:
    password = os.environ["FRAS_SSH_PASS"]
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        HOST,
        username=USER,
        password=password,
        timeout=20,
        look_for_keys=False,
        allow_agent=False,
    )
    return ssh


def ssh_run(ssh: paramiko.SSHClient, command: str, timeout: int = 900) -> None:
    print(f"\n[REMOTE] {command}\n")
    stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    for line in iter(stdout.readline, ""):
        print(line, end="")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    if err:
        print(err, file=sys.stderr)
    if code != 0:
        raise RuntimeError(f"Remote command failed with exit code {code}: {command}")


def upload(ssh: paramiko.SSHClient, archive_path: Path) -> None:
    print(f"[UPLOAD] {archive_path} -> {REMOTE_TAR}")
    sftp = ssh.open_sftp()
    try:
        sftp.put(str(archive_path), REMOTE_TAR)
    finally:
        sftp.close()


def main() -> int:
    archive_path = build_archive()
    print(f"[LOCAL] Built deploy archive: {archive_path} ({archive_path.stat().st_size:,} bytes)")

    ssh = connect()
    try:
        upload(ssh, archive_path)
        commands = [
            f"mkdir -p {REMOTE_DIR} /home/{USER}/deploy_backups",
            (
                f"if [ -d {REMOTE_DIR} ]; then "
                f"cd {REMOTE_DIR} && "
                "if [ -f docker-compose.v2.yml ]; then "
                "mkdir -p deployment/backups && "
                "docker compose -f docker-compose.v2.yml exec -T db "
                "pg_dump -U ${POSTGRES_USER:-fras_v2} ${POSTGRES_DB:-fras_v2} "
                "> deployment/backups/pre_v2_redeploy_$(date +%Y%m%d_%H%M%S).sql || true; "
                "fi; "
                "fi"
            ),
            (
                f"cd {REMOTE_DIR} && "
                "docker compose -f docker-compose.v2.yml down --remove-orphans || true && "
                "docker compose -f docker-compose.prod.yml down --remove-orphans || true"
            ),
            f"cd {REMOTE_DIR} && tar -xzf {REMOTE_TAR}",
            f"cd {REMOTE_DIR} && cp -n .env.v2.example .env",
            (
                f"cd {REMOTE_DIR} && "
                "python3 - <<'PY'\n"
                "from pathlib import Path\n"
                "p=Path('.env')\n"
                "text=p.read_text() if p.exists() else ''\n"
                "updates={\n"
                "'POSTGRES_USER':'fras_v2',\n"
                "'POSTGRES_PASSWORD':'change-this-v2-password',\n"
                "'POSTGRES_DB':'fras_v2',\n"
                "'POSTGRES_PORT':'5432',\n"
                "'TZ':'Asia/Manila',\n"
                "'DATABASE_URL':'postgresql://fras_v2:change-this-v2-password@db:5432/fras_v2',\n"
                "'JWT_SECRET':'fras-v2-demo-secret-change-after-demo',\n"
                "'JWT_EXPIRE_MINUTES':'1440',\n"
                "'FRAS_MODE':'v2',\n"
                "'DATASET_PATH':'/app/dataset',\n"
                "'CORS_ORIGINS':'http://92.205.61.8,http://92.205.61.8:8080,https://92.205.61.8',\n"
                "'BACKEND_PORT':'8000',\n"
                "'FRONTEND_PORT':'8080',\n"
                "}\n"
                "lines=[]\n"
                "seen=set()\n"
                "for line in text.splitlines():\n"
                "    if '=' in line and not line.lstrip().startswith('#'):\n"
                "        k=line.split('=',1)[0]\n"
                "        if k in updates:\n"
                "            lines.append(f'{k}={updates[k]}')\n"
                "            seen.add(k)\n"
                "        else:\n"
                "            lines.append(line)\n"
                "    else:\n"
                "        lines.append(line)\n"
                "for k,v in updates.items():\n"
                "    if k not in seen:\n"
                "        lines.append(f'{k}={v}')\n"
                "p.write_text('\\n'.join(lines)+'\\n')\n"
                "PY"
            ),
            f"cd {REMOTE_DIR} && docker compose -f docker-compose.v2.yml --env-file .env up -d --build",
            f"cd {REMOTE_DIR} && docker compose -f docker-compose.v2.yml exec -T backend python database/init_v2_database.py --force",
            (
                f"cd {REMOTE_DIR} && docker compose -f docker-compose.v2.yml exec -T backend "
                "python database/seed_v2_integration_data.py "
                "--docx /app/deployment/seed/FRAS-prof-database.docx "
                "--enroll-all-active-classes"
            ),
            f"cd {REMOTE_DIR} && docker compose -f docker-compose.v2.yml exec -T backend python database/clear_v2_session_data.py --force",
            f"cd {REMOTE_DIR} && docker compose -f docker-compose.v2.yml exec -T backend python database/clear_v2_face_data.py --force",
            f"cd {REMOTE_DIR} && docker compose -f docker-compose.v2.yml exec -T backend python database/check_v2_database.py",
            f"cd {REMOTE_DIR} && docker compose -f docker-compose.v2.yml exec -T backend python database/verify_v2_integration_seed.py",
            f"cd {REMOTE_DIR} && docker compose -f docker-compose.v2.yml exec -T backend python database/check_v2_roster_counts.py",
            f"cd {REMOTE_DIR} && docker compose -f docker-compose.v2.yml exec -T db psql -U fras_v2 -d fras_v2 -c \"SHOW timezone;\"",
            f"cd {REMOTE_DIR} && docker compose -f docker-compose.v2.yml ps",
            "curl -fsSI http://127.0.0.1:8080/ | head -n 5",
            "curl -fsS http://127.0.0.1:8000/docs >/dev/null && echo backend_docs_ok",
        ]
        for command in commands:
            ssh_run(ssh, command)
    finally:
        ssh.close()
        shutil.rmtree(archive_path.parent, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
