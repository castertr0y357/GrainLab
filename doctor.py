#!/usr/bin/env python
"""
Pre-flight diagnostics command validating database migrations,
environment setups, network loops, and local LLM endpoint reachability.
"""
import os
import sys
import socket
import subprocess
import urllib.parse
import urllib.request
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grainlab.settings')
try:
    django.setup()
except Exception as e:
    print(f"[Error] [Doctor] - Config - Failed to initialize Django settings: {e}")
    sys.exit(1)

from django.db import connections
from django.db.migrations.executor import MigrationExecutor
from apps.core.models import SystemSetting


def check_env():
    """Verify that required settings are in place."""
    print("[Info] Checking environment configurations...")
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key or secret_key.startswith("django-insecure-placeholder"):
        print("[Warning] [Doctor] - Config - SECRET_KEY is set to default/unsafe placeholder.")
    else:
        print("[Success] [Doctor] - Config - SECRET_KEY is set and verified.")
        
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        print(f"[Success] [Doctor] - Config - DATABASE_URL is set (PostgreSQL active).")
    else:
        print("[Warning] [Doctor] - Config - DATABASE_URL is missing. Using fallback SQLite database.")


def check_database():
    """Check database reachability and migrations status."""
    print("\n[Database] Checking database reachability and migrations...")
    db_conn = connections['default']
    try:
        db_conn.ensure_connection()
        print("[Success] [Doctor] - Database - Connection to database established successfully.")
    except Exception as e:
        print(f"[Error] [Doctor] - Database - Connection failed: {e}")
        return False

    try:
        executor = MigrationExecutor(db_conn)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if plan:
            print(f"[Error] [Doctor] - Database - Unapplied migrations found: {len(plan)} pending.")
            for migration, backward in plan:
                print(f"   - Pending: {migration}")
            return False
        else:
            print("[Success] [Doctor] - Database - All migrations are fully applied.")
            return True
    except Exception as e:
        print(f"[Error] [Doctor] - Database - Failed checking migrations graph: {e}")
        return False


def check_gemma_api():
    """Check reachability of local Gemma API endpoint."""
    print("\n[AI] Checking local LLM Gemma connection status...")
    ai_enabled = SystemSetting.get_val("ai_enabled", "False") == "True"
    url = SystemSetting.get_val("ai_api_url", "http://host.docker.internal:11434/v1")
    
    if not ai_enabled:
        print("[Info] [Doctor] - AI - Local AI (Gemma) is currently disabled. Recipe fallbacks will execute.")
        return

    # Clean the completions URL
    completions_url = url.rstrip("/") + "/chat/completions"
    print(f"Connecting to AI endpoint: {completions_url}...")
    
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 11434
    
    # Try raw socket connection first to check reachability
    try:
        socket.setdefaulttimeout(2)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        print(f"[Success] [Doctor] - Network - Host '{host}' is reachable on port {port}.")
    except Exception as e:
        print(f"[Error] [Doctor] - Network - Port {port} on host '{host}' is unreachable: {e}")
        print("[Warning] [Doctor] - AI - Gemma is offline. Fallback engines will handle sensory calibration.")
        return

    # Send a small request to check status
    try:
        req = urllib.request.Request(
            completions_url,
            data=b'{"model":"gemma:12b","messages":[{"role":"user","content":"Ping"}]}',
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=3) as response:
            if response.status == 200:
                print("[Success] [Doctor] - AI - Gemma endpoint responded with status 200.")
            else:
                print(f"[Warning] [Doctor] - AI - Gemma endpoint responded with status {response.status}.")
    except Exception as e:
        print(f"[Warning] [Doctor] - AI - Failed during endpoint ping test: {e}")
        print("[Info] Check that your model name matches 'gemma:12b' or customize it in settings.")


def check_dependency_audit():
    """Verify that dependencies are secure using pip-audit."""
    print("\n[Security] Auditing dependencies for vulnerabilities...")
    try:
        # Check if pip-audit is installed
        result = subprocess.run(["pip-audit", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("[Warning] [Doctor] - Security - pip-audit failed to execute. Install via 'pip install pip-audit'.")
            return True
    except FileNotFoundError:
        print("[Warning] [Doctor] - Security - pip-audit is not installed. Install via 'pip install pip-audit' to audit dependencies.")
        return True

    # Run audit on requirements.txt
    try:
        audit_res = subprocess.run(["pip-audit", "-r", "requirements.txt"], capture_output=True, text=True)
        if audit_res.returncode == 0:
            print("[Success] [Doctor] - Security - No known vulnerabilities detected in requirements.txt.")
            return True
        else:
            print("[Error] [Doctor] - Security - Known vulnerabilities detected:")
            print(audit_res.stdout)
            print(audit_res.stderr)
            return False
    except Exception as e:
        print(f"[Warning] [Doctor] - Security - Dependency audit check encountered an error: {e}")
        return True


def main():
    print("=" * 60)
    print("GRAINLAB SYSTEM DIAGNOSTICS")
    print("=" * 60)
    
    check_env()
    db_ok = check_database()
    check_gemma_api()
    audit_ok = check_dependency_audit()
    
    print("\n" + "=" * 60)
    if db_ok and audit_ok:
        print("[Success] DIAGNOSTICS COMPLETED: Workspace is healthy and ready to compile!")
        sys.exit(0)
    else:
        print("[Error] DIAGNOSTICS COMPLETED: One or more critical systems are misconfigured or vulnerable.")
        sys.exit(1)


if __name__ == '__main__':
    main()
