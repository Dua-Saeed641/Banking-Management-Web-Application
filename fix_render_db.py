"""
Cleans up old bad transaction records and adds the missing constraint.
Usage:
    python fix_render_db.py "postgresql://user:password@host/dbname"
"""
import sys

def fix_db(database_url):
    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        print("ERROR: sqlalchemy not installed. Run: pip install sqlalchemy")
        sys.exit(1)

    url = database_url.replace("postgres://", "postgresql://", 1)
    engine = create_engine(url)

    with engine.connect() as conn:
        # Show bad transactions
        result = conn.execute(text(
            "SELECT transaction_id, amount, transaction_type FROM transactions WHERE amount > 1000000.00;"
        ))
        bad_txns = result.fetchall()

        if not bad_txns:
            print("No bad transactions found.")
        else:
            print(f"Found {len(bad_txns)} transaction(s) with amounts over the limit:")
            for r in bad_txns:
                print(f"  txn_id={r[0]}, amount={r[1]}, type={r[2]}")

            conn.execute(text(
                "DELETE FROM transactions WHERE amount > 1000000.00;"
            ))
            conn.commit()
            print(f"Deleted {len(bad_txns)} bad transaction record(s).")

        # Now try adding the constraint
        print("\nAdding ck_txn_amount_max constraint...")
        try:
            conn.execute(text(
                "ALTER TABLE transactions ADD CONSTRAINT ck_txn_amount_max CHECK (amount <= 1000000.00);"
            ))
            conn.commit()
            print("  [OK] Constraint added successfully.")
        except Exception as e:
            conn.rollback()
            print(f"  [SKIP] Already exists or error: {e}")

        # Verify final state
        print("\nFinal account balances:")
        for row in conn.execute(text("SELECT account_id, user_id, balance FROM bank_accounts;")).fetchall():
            print(f"  account_id={row[0]}, user_id={row[1]}, balance={row[2]}")

    print("\nDone!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_render_db.py \"<EXTERNAL_DATABASE_URL>\"")
        sys.exit(1)
    fix_db(sys.argv[1])
