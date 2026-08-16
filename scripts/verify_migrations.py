import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parents[1]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from backend.app.core.config import settings
from backend.app.db.base import Base

import socket

def is_postgres_listening(host: str = "localhost", port: int = 5432) -> bool:
    """Check TCP connection to PostgreSQL port with 0.5s timeout."""
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def run_alembic_verification():
    print("==================================================")
    print("ALEMBIC MIGRATION LIFECYCLE VERIFICATION")
    print("==================================================")

    # Use SQLite file for standalone migration verification if Postgres not listening
    if is_postgres_listening(settings.POSTGRES_SERVER, settings.POSTGRES_PORT):
        target_uri = settings.SQLALCHEMY_DATABASE_URI
        db_type = "PostgreSQL"
    else:
        target_uri = "sqlite:///scripts/migration_test.db"
        db_type = "SQLite (Migration Standalone Test DB - PostgreSQL server unreachable on host)"


    print(f"Target Database Engine: {db_type}")
    print(f"Connection URI: {target_uri}")

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", target_uri)
    test_engine = create_engine(target_uri)

    # Clean up any pre-existing test db tables and migration tracking table
    Base.metadata.drop_all(bind=test_engine)
    with test_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
        conn.commit()


    # STEP 1: Upgrade to head
    print("\n--- Step 1: Alembic Upgrade to 'head' ---")
    command.upgrade(alembic_cfg, "head")
    print("Result: Upgrade command executed successfully.")

    # STEP 2: Confirm schema exists
    print("\n--- Step 2: Confirm Expected Schema Exists ---")
    inspector = inspect(test_engine)
    tables = inspector.get_table_names()
    print(f"Tables found: {tables}")
    assert "users" in tables, "Table 'users' missing after upgrade."
    assert "oauth_accounts" in tables, "Table 'oauth_accounts' missing after upgrade."
    assert "sessions" in tables, "Table 'sessions' missing after upgrade."
    assert "email_threads" in tables, "Table 'email_threads' missing after upgrade."
    assert "email_messages" in tables, "Table 'email_messages' missing after upgrade."
    assert "attachments" in tables, "Table 'attachments' missing after upgrade."
    assert "gmail_sync_states" in tables, "Table 'gmail_sync_states' missing after upgrade."
    print("Result: Schema verification PASSED (all 7 tables exist).")

    # STEP 3: Downgrade to base
    print("\n--- Step 3: Alembic Downgrade to 'base' ---")
    command.downgrade(alembic_cfg, "base")
    print("Result: Downgrade command executed successfully.")

    # STEP 4: Confirm schema reverted
    print("\n--- Step 4: Confirm Schema Reverted ---")
    inspector = inspect(test_engine)
    reverted_tables = inspector.get_table_names()
    print(f"Tables found after downgrade: {reverted_tables}")
    assert "users" not in reverted_tables, "Table 'users' still exists after downgrade."
    assert "oauth_accounts" not in reverted_tables, "Table 'oauth_accounts' still exists after downgrade."
    assert "sessions" not in reverted_tables, "Table 'sessions' still exists after downgrade."
    assert "email_threads" not in reverted_tables, "Table 'email_threads' still exists after downgrade."
    assert "email_messages" not in reverted_tables, "Table 'email_messages' still exists after downgrade."
    assert "attachments" not in reverted_tables, "Table 'attachments' still exists after downgrade."
    assert "gmail_sync_states" not in reverted_tables, "Table 'gmail_sync_states' still exists after downgrade."
    print("Result: Schema reversion PASSED (all tables dropped).")

    # STEP 5: Upgrade again successfully
    print("\n--- Step 5: Alembic Upgrade Again to 'head' ---")
    command.upgrade(alembic_cfg, "head")
    print("Result: Re-upgrade command executed successfully.")

    inspector = inspect(test_engine)
    final_tables = inspector.get_table_names()
    print(f"Tables found after re-upgrade: {final_tables}")
    assert "users" in final_tables
    assert "oauth_accounts" in final_tables
    assert "sessions" in final_tables
    assert "email_threads" in final_tables
    assert "email_messages" in final_tables
    assert "attachments" in final_tables
    assert "gmail_sync_states" in final_tables
    print("Result: Final schema re-upgrade PASSED.")



    # Cleanup temporary migration test db file if created
    test_engine.dispose()
    temp_db_file = Path("scripts/migration_test.db")
    if temp_db_file.exists():
        temp_db_file.unlink()

    print("\n==================================================")
    print("ALL ALEMBIC MIGRATION LIFECYCLE TESTS PASSED")
    print("==================================================")

if __name__ == "__main__":
    run_alembic_verification()
