#!/usr/bin/env python3
"""
Provision the print_service user in ArangoDB and write the password file
for Docker Compose.

Can be run at any time — during initial installation or later when adding
the print service to an existing deployment.  Re-running the script rotates
the password (update the file, restart the container).

The script automatically runs inside a throwaway API container (via Docker)
so no Python dependencies are needed on the host.  Pass --local to skip
the Docker wrapper and run directly (requires python-arango and passlib).

Usage:
    python3 setup_print_service.py                        # runs in container
    python3 setup_print_service.py --db-name PROGRESS_DEV # extra flags
    python3 setup_print_service.py --local                # run on host directly
"""

import os
import subprocess
import sys


_INSIDE_CONTAINER = os.environ.get("_PRINT_SETUP_CONTAINER") == "1"

CONFIG_DIR = os.environ.get("CONFIG_DIR", "/opt/progress/config")


def run_in_container() -> None:
    """Re-exec this script inside the API container."""
    try:
        api_image = subprocess.check_output(
            ["docker", "service", "inspect", "progress_api",
             "--format", "{{.Spec.TaskTemplate.ContainerSpec.Image}}"],
            text=True, stderr=subprocess.PIPE,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: could not read image from progress_api service. Is the stack running?", file=sys.stderr)
        sys.exit(1)

    script_path = os.path.abspath(__file__)

    # Strip --local if someone accidentally combined both
    forwarded_args = [a for a in sys.argv[1:] if a != "--local"]

    # Replace the current process with a new one that runs the script inside the API container
    os.execvp("docker", [
        "docker", "run", "--rm", "-it",
        "--network", "progress",
        "-e", "_PRINT_SETUP_CONTAINER=1",
        "-v", f"{script_path}:/setup_print_service.py:ro",
        "-v", f"{CONFIG_DIR}:/output",
        api_image,
        "python3", "/setup_print_service.py", "--local",
        "--db-host", "http://db:8529",
        "--output", "/output/.print_service_pwd",
        *forwarded_args,
    ])


# ---------------------------------------------------------------------------
# Everything below runs inside the container (or with --local on the host)
# ---------------------------------------------------------------------------

def _run_local() -> None:
    import argparse
    import getpass
    import secrets

    import bcrypt
    from arango import ArangoClient

    PRINT_SERVICE_USER = dict(
        username="print_service",
        name="Print",
        surname="Service",
        scope="print_service",
        site_key="0",
        active=True,
        reset_password=False,
    )

    def upsert_print_service_user(db, password_hash: str) -> str:
        """Create or update the print_service user. Returns 'created' or 'updated'."""
        col = db.collection("User")
        existing = list(col.find({"username": "print_service"}, limit=1))

        if existing:
            doc = existing[0]
            col.update({
                "_key": doc["_key"],
                "psw_hash": password_hash,
                "reset_password": False,
                "scope": PRINT_SERVICE_USER["scope"],
                "active": True,
            })
            return "updated"

        col.insert({**PRINT_SERVICE_USER, "psw_hash": password_hash})
        return "created"

    def write_password_file(path: str, password: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
        try:
            os.write(fd, password.encode())
        finally:
            os.close(fd)
        os.chmod(path, 0o644)

    p = argparse.ArgumentParser(
        description="Provision the print_service account and write the password file.",
    )
    p.add_argument("--local", action="store_true", help="Run directly instead of inside a Docker container")
    p.add_argument("--db-host", default="http://localhost:8529", help="ArangoDB URL (default: http://localhost:8529)")
    p.add_argument("--db-name", default="PROGRESS_PROD", help="Application database name (default: PROGRESS_PROD)")
    p.add_argument("--db-user", default="root", help="ArangoDB user (default: root)")
    p.add_argument("--db-password", default=None, help="ArangoDB password (prompted securely if omitted)")
    p.add_argument("--output", default="/opt/progress/config/.print_service_pwd", help="Path to write the password file")
    args = p.parse_args()

    if args.db_password is None:
        args.db_password = getpass.getpass("ArangoDB password: ")

    password = secrets.token_hex(16)
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    client = ArangoClient(hosts=args.db_host)
    db = client.db(args.db_name, username=args.db_user, password=args.db_password)

    action = upsert_print_service_user(db, password_hash)
    write_password_file(args.output, password)

    print(f"print_service user {action} in {args.db_name}")
    print(f"Password written to {args.output}")
    print()
    print("Next steps:")
    print()
    print("  A) Same host (Docker Compose):")
    print("     cd /opt/progress/config && docker compose -f print.yaml up -d")
    print()
    print("  B) Remote Windows host:")
    print(f"     1. Copy the password from {args.output} into the .env file")
    print("        as PROGRESS_PRINT_SERVICE_API_PASSWORD")
    print("     2. Run install.bat as Administrator")


if __name__ == "__main__":
    if "--local" in sys.argv or _INSIDE_CONTAINER:
        _run_local()
    else:
        run_in_container()
