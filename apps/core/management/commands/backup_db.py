import gzip
import os
import shutil
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generates a compressed, timestamped database backup."

    def handle(self, *args, **options):
        # Resolve target backup folder
        backup_dir = settings.BASE_DIR / "backups"
        backup_dir.mkdir(exist_ok=True)

        db_conf = settings.DATABASES["default"]
        engine = db_conf["ENGINE"]
        timestamp = time.strftime("%Y%m%d-%H%M%S")

        backup_filename = f"backup-{timestamp}.sql.gz"
        backup_path = backup_dir / backup_filename

        self.stdout.write(f"Starting database backup for engine: {engine}...")

        if "sqlite3" in engine:
            db_path = Path(db_conf["NAME"])
            if not db_path.exists():
                self.stderr.write(self.style.ERROR(f"SQLite DB file {db_path} does not exist."))
                return

            try:
                # Copy file and compress it
                with open(db_path, "rb") as f_in, gzip.open(backup_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

                # Limit permissions
                try:
                    backup_path.chmod(0o600)
                except Exception as e:
                    self.stderr.write(
                        self.style.WARNING(f"Warning: Could not set strict permissions on backup file: {e}")
                    )

                self.stdout.write(self.style.SUCCESS(f"Successfully backed up SQLite database to: {backup_path}"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"SQLite backup failed: {e}"))
                return

        elif "postgresql" in engine:
            # PostgreSQL dump using pg_dump
            db_name = db_conf["NAME"]
            db_user = db_conf["USER"]
            db_pass = db_conf["PASSWORD"]
            db_host = db_conf["HOST"]
            db_port = db_conf["PORT"]

            # Setup environment with PG_PASSWORD
            env = os.environ.copy()
            if db_pass:
                env["PGPASSWORD"] = db_pass

            cmd = [
                "pg_dump",
                "-h",
                db_host or "localhost",
                "-p",
                str(db_port or 5432),
                "-U",
                db_user,
                "-F",
                "c",  # custom format (compressed binary format of postgres)
                "-f",
                str(backup_dir / f"backup-{timestamp}.dump"),
                "--",
                db_name,
            ]

            import subprocess

            try:
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)  # nosec B603 B404
                if result.returncode == 0:
                    dump_path = backup_dir / f"backup-{timestamp}.dump"
                    # Compress dump file
                    with open(dump_path, "rb") as f_in, gzip.open(backup_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                    os.remove(dump_path)

                    try:
                        backup_path.chmod(0o600)
                    except Exception as e:
                        self.stderr.write(
                            self.style.WARNING(f"Warning: Could not set strict permissions on backup file: {e}")
                        )
                    self.stdout.write(
                        self.style.SUCCESS(f"Successfully backed up PostgreSQL database to: {backup_path}")
                    )
                else:
                    self.stderr.write(self.style.ERROR(f"pg_dump failed: {result.stderr}"))
            except FileNotFoundError:
                self.stderr.write(
                    self.style.ERROR("pg_dump utility not found. Please install PostgreSQL client tools.")
                )
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"PostgreSQL backup failed: {e}"))

        else:
            self.stderr.write(self.style.ERROR(f"Unsupported database engine for backup: {engine}"))
            return

        # Retention Cleanup (Delete backups older than 30 days)
        now = time.time()
        retention_sec = 30 * 24 * 60 * 60  # 30 days
        for f in backup_dir.glob("backup-*.sql.gz"):
            try:
                if now - f.stat().st_mtime > retention_sec:
                    f.unlink()
                    self.stdout.write(f"Pruned expired backup file: {f.name}")
            except Exception as e:
                self.stderr.write(self.style.WARNING(f"Failed pruning backup file {f.name}: {e}"))
