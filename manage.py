#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys


def main():
    """Run administrative tasks."""
    # Bootstrap .env if missing
    import secrets
    from pathlib import Path

    base_dir = Path(__file__).resolve().parent
    env_file = base_dir / ".env"
    env_example = base_dir / ".env.example"
    if not env_file.exists():
        if env_example.exists():
            content = env_example.read_text()
            # Generate a secure key
            new_key = secrets.token_urlsafe(50)
            content = content.replace("django-insecure-placeholder-generate-key-here", new_key)

            # Generate a secure DB password
            new_db_pass = secrets.token_urlsafe(32)
            content = content.replace("postgres_dev_secure_password_please_change", new_db_pass)

            env_file.write_text(content)
            try:
                env_file.chmod(0o600)
            except Exception:
                pass

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "grainlab.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    if "test" in sys.argv:
        import django.template.context

        def safe_copy(self):
            duplicate = object.__new__(type(self))
            duplicate.__dict__.update(self.__dict__)
            duplicate.dicts = self.dicts[:]
            return duplicate

        django.template.context.BaseContext.__copy__ = safe_copy

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
