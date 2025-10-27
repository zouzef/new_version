import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common_function import format_date  # Your custom date formatting function

def insert_account_subject(conn, account_subject_data, dry_run=False):
    """
    Insert account_subject data into MariaDB.
    - Inserts only new records.
    - Skips if record ID already exists.
    """
    result = {"success_count":0, "skipped_count":0, "error_count":0, "errors":[], "total_processed":0}
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        created_data = account_subject_data.get("created", [])
        result["total_processed"] = len(created_data)

        if not created_data:
            print("No account_subject records to process")
            return result

        print(f"Processing {len(created_data)} new account_subject record(s)...")

        for i, rec in enumerate(created_data, 1):
            try:
                rec_id = rec.get("id")
                if not rec_id:
                    raise ValueError("Missing required field: id")

                # Check if record exists
                cursor.execute("SELECT id FROM account_subject WHERE id=%s", (rec_id,))
                if cursor.fetchone():
                    print(f"⏭️ Account_subject ID {rec_id} already exists — skipping insert.")
                    result["skipped_count"] += 1
                    continue

                data = {
                    "account_id": rec.get("accountId"),
                    "subject_config_id": rec.get("subjectConfigId"),
                    "other_subject": rec.get("otherSubject"),
                    "status": 1 if rec.get("status", True) else 0,
                    "description": rec.get("description", ""),
                    "enabled": 1 if rec.get("enabled", True) else 0,
                    "releaseToken": 1 if rec.get("releaseToken", False) else 0,
                    "useToken": rec.get("useToken"),
                    "created_at": format_date(rec.get("createdAt")),
                    "updated_at": format_date(rec.get("updatedAt")),
                    "timestamp": format_date(rec.get("timestamp"))
                }

                print(f"Inserting account_subject {i}/{len(created_data)} - ID {rec_id}")

                if not dry_run:
                    cursor.execute("""
                        INSERT INTO account_subject (
                            id, account_id, subject_config_id, other_subject, status,
                            description, enabled, created_at, updated_at, timestamp,
                            releaseToken, useToken
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        rec_id, data["account_id"], data["subject_config_id"], data["other_subject"],
                        data["status"], data["description"], data["enabled"], data["created_at"],
                        data["updated_at"], data["timestamp"], data["releaseToken"], data["useToken"]
                    ))

                result["success_count"] += 1
                print(f"✔ Account_subject ID {rec_id} {'would be inserted (dry run)' if dry_run else 'inserted successfully'}")

            except Exception as err:
                print(f"❌ Error inserting account_subject ID {rec.get('id', 'unknown')}: {err}")
                result["error_count"] += 1
                result["errors"].append({"account_subject_id": rec.get("id", "unknown"), "error": str(err), "record_number": i})
                continue

        if not dry_run:
            conn.commit()

        print(f"\n✅ Inserted: {result['success_count']}, ⏭️ Skipped: {result['skipped_count']}, ⚠️ Errors: {result['error_count']}")

    except Exception as err:
        print(f"💥 Unexpected database error: {err}")
        if not dry_run:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()

    return result


def update_account_subject(conn, account_subject_data, dry_run=False):
    """
    Update account_subject data in MariaDB.
    - Skips update if data is identical.
    """
    result = {"success_count":0, "skipped_count":0, "error_count":0, "errors":[], "total_processed":0}
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        updated_data = account_subject_data.get("updated", [])
        result["total_processed"] = len(updated_data)

        if not updated_data:
            print("No account_subject records to update")
            return result

        print(f"Updating {len(updated_data)} account_subject record(s)...")

        for i, rec in enumerate(updated_data, 1):
            try:
                rec_id = rec.get("id")
                if not rec_id:
                    raise ValueError("Missing required field: id")

                new_data = {
                    "account_id": rec.get("accountId"),
                    "subject_config_id": rec.get("subjectConfigId"),
                    "other_subject": rec.get("otherSubject"),
                    "status": 1 if rec.get("status", True) else 0,
                    "description": rec.get("description", ""),
                    "enabled": 1 if rec.get("enabled", True) else 0,
                    "releaseToken": 1 if rec.get("releaseToken", False) else 0,
                    "useToken": rec.get("useToken"),
                    "updated_at": format_date(rec.get("updatedAt")),
                    "timestamp": format_date(rec.get("timestamp"))
                }

                # Fetch existing record
                cursor.execute("SELECT * FROM account_subject WHERE id=%s", (rec_id,))
                existing = cursor.fetchone()
                if not existing:
                    print(f"⚠️ Account_subject ID {rec_id} not found — skipping update")
                    result["skipped_count"] += 1
                    continue

                # Compare new data vs existing
                identical = True
                for key, value in new_data.items():
                    old_value = str(existing.get(key)) if existing.get(key) is not None else None
                    new_value = str(value) if value is not None else None
                    if old_value != new_value:
                        identical = False
                        break

                if identical:
                    print(f"⏭️ Account_subject ID {rec_id} — no changes detected (skipped)")
                    result["skipped_count"] += 1
                    continue

                print(f"Updating account_subject ID {rec_id} {'(dry run)' if dry_run else ''}")

                if not dry_run:
                    cursor.execute("""
                        UPDATE account_subject SET
                            account_id=%s, subject_config_id=%s, other_subject=%s,
                            status=%s, description=%s, enabled=%s,
                            releaseToken=%s, useToken=%s, updated_at=%s, timestamp=%s
                        WHERE id=%s
                    """, (
                        new_data["account_id"], new_data["subject_config_id"], new_data["other_subject"],
                        new_data["status"], new_data["description"], new_data["enabled"],
                        new_data["releaseToken"], new_data["useToken"],
                        new_data["updated_at"], new_data["timestamp"], rec_id
                    ))

                result["success_count"] += 1
                print(f"✔ Account_subject ID {rec_id} {'would be updated (dry run)' if dry_run else 'updated successfully'}")

            except Exception as err:
                print(f"❌ Error updating account_subject ID {rec.get('id', 'unknown')}: {err}")
                result["error_count"] += 1
                result["errors"].append({"account_subject_id": rec.get("id", "unknown"), "error": str(err), "record_number": i})
                continue

        if not dry_run:
            conn.commit()

        print(f"\n✅ Updated: {result['success_count']}, ⏭️ Skipped: {result['skipped_count']}, ⚠️ Errors: {result['error_count']}")

    except Exception as err:
        print(f"💥 Unexpected database error: {err}")
        if not dry_run:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()

    return result
