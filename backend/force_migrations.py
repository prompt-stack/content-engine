#!/usr/bin/env python3
"""
Force run database migrations on Railway.

This script manually runs alembic migrations to ensure the database is up to date.
Use this when migrations haven't been automatically applied.
"""
import subprocess
import sys

def main():
    print("🔄 Forcing database migrations...")

    try:
        # Show current version
        print("\n📊 Current database version:")
        subprocess.run(["alembic", "current"], check=True)

        # Show pending migrations
        print("\n📋 Migration history:")
        subprocess.run(["alembic", "history"], check=True)

        # Upgrade to head
        print("\n⬆️  Upgrading to latest version...")
        result = subprocess.run(["alembic", "upgrade", "head"], check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        # Show new current version
        print("\n✅ New database version:")
        subprocess.run(["alembic", "current"], check=True)

        print("\n🎉 Migrations complete!")
        return 0

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Migration failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
