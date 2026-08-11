from app.db.session import SessionLocal
from sqlalchemy import text

def update_enum():
    db = SessionLocal()
    new_values = [
        "true_false_not_given",
        "matching_headings",
        "matching_features",
        "sentence_completion",
        "summary_completion",
        "table_completion",
        "diagram_label_completion",
        "multiple_choice_ielts"
    ]
    try:
        # PostgreSQL specific query to get enum values
        result = db.execute(text("SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid WHERE typname = 'componenttype';"))
        existing = [row[0] for row in result.fetchall()]
        print("Existing ENUM values:", existing)

        # Alter type requires outside of transaction block, so we set isolation level
        db.connection().connection.set_isolation_level(0) # AUTOCOMMIT
        
        for val in new_values:
            if val not in existing:
                try:
                    db.execute(text(f"ALTER TYPE componenttype ADD VALUE '{val}';"))
                    print(f"Added {val}")
                except Exception as e:
                    print(f"Failed to add {val}: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_enum()
