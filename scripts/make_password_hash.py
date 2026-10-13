"""
Generate ADMIN_PASSWORD_HASH for .env (run: python scripts/make_password_hash.py).
Uses the same PBKDF2 scheme as app/auth.py — no extra dependencies.
"""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.auth import hash_password

if __name__ == "__main__":
    pw = getpass.getpass("New admin password: ")
    pw2 = getpass.getpass("Confirm password: ")
    if not pw or pw != pw2:
        print("Passwords do not match or are empty.")
        raise SystemExit(1)
    print()
    print("Add this line to your .env (never commit .env):")
    print(f"ADMIN_PASSWORD_HASH={hash_password(pw)}")
