import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'download_images'))
from download_images.download_images_local import download_image
from common_function import format_date

def insert_account(conn, token, account_data):
    """
    Insert account data into MariaDB.
    - Inserts only new records.
    - Skips if record ID already exists.
    """
    result = {"success_count": 0, "skipped_count": 0, "error_count": 0, "errors": [], "total_processed": 0}
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        created_accounts = account_data.get("created", [])
        result["total_processed"] = len(created_accounts)

        print(f"Processing {len(created_accounts)} new account record(s)...")

        for i, account in enumerate(created_accounts, 1):
            try:
                account_id = account.get("id")
                if not account_id:
                    raise ValueError("Missing required field: id")

                # Check if already exists
                cursor.execute("SELECT id FROM account WHERE id = %s", (account_id,))
                if cursor.fetchone():
                    print(f"⏭️ Account ID {account_id} already exists — skipping insert.")
                    result["skipped_count"] += 1
                    continue

                name = account.get("name", "")
                file_link = account.get("image", "")
                if file_link:
                    download_image(token, file_link)
                status = account.get("status", True)
                created_at = format_date(account.get("createdAt"))
                updated_at = format_date(account.get("updatedAt"))
                timestamp = format_date(account.get("timestamp"))

                print(f"Inserting account {i}/{len(created_accounts)} - ID {account_id}")

                cursor.execute("""
                    INSERT INTO account (id, name, file_link, status, created_at, updated_at, timestamp)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (account_id, name, file_link, status, created_at, updated_at, timestamp))

                result["success_count"] += 1
                print(f"✔ Account ID {account_id} inserted successfully")

            except Exception as err:
                print(f"❌ Error inserting account ID {account.get('id', 'unknown')}: {err}")
                result["error_count"] += 1
                result["errors"].append({"account_id": account.get("id", "unknown"), "error": str(err), "record_number": i})
                continue

        conn.commit()
        print(f"\n✅ Inserted: {result['success_count']}, ⏭️ Skipped: {result['skipped_count']}, ⚠️ Errors: {result['error_count']}")

    except Exception as err:
        print(f"💥 Unexpected database error: {err}")
        conn.rollback()
    finally:
        if cursor:
            cursor.close()

    return result


def update_account(conn, account_data):
    """
    Update account data in MariaDB.
    - Skips update if data is identical.
    """
    result = {"success_count": 0, "skipped_count": 0, "error_count": 0, "errors": [], "total_processed": 0}
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        updated_accounts = account_data.get("updated", [])
        result["total_processed"] = len(updated_accounts)

        if not updated_accounts:
            print("No account records to update")
            return result

        print(f"Updating {len(updated_accounts)} account record(s)...")

        for i, account in enumerate(updated_accounts, 1):
            try:
                account_id = account.get("id")
                if not account_id:
                    raise ValueError("Missing required field: id")

                # Fetch existing record
                cursor.execute("SELECT * FROM account WHERE id = %s", (account_id,))
                existing = cursor.fetchone()
                if not existing:
                    print(f"⚠️ Account ID {account_id} not found — skipping update")
                    result["skipped_count"] += 1
                    continue

                new_data = {
                    "name": account.get("name", ""),
                    "file_link": account.get("image", ""),
                    "status": account.get("status", True),
                    "created_at": format_date(account.get("createdAt")),
                    "updated_at": format_date(account.get("updatedAt")),
                    "timestamp": format_date(account.get("timestamp"))
                }

                # Compare new data vs existing
                identical = True
                for key, value in new_data.items():
                    old_value = str(existing.get(key)) if existing.get(key) is not None else None
                    new_value = str(value) if value is not None else None
                    if old_value != new_value:
                        identical = False
                        break

                if identical:
                    print(f"⏭️ Account ID {account_id} — no changes detected (skipped)")
                    result["skipped_count"] += 1
                    continue

                print(f"Updating account {i}/{len(updated_accounts)} - ID {account_id}")

                cursor.execute("""
                    UPDATE account SET
                        name=%s, file_link=%s, status=%s,
                        created_at=%s, updated_at=%s, timestamp=%s
                    WHERE id=%s
                """, (new_data["name"], new_data["file_link"], new_data["status"],
                      new_data["created_at"], new_data["updated_at"], new_data["timestamp"], account_id))

                result["success_count"] += 1
                print(f"✔ Account ID {account_id} updated successfully")

            except Exception as err:
                print(f"❌ Error updating account ID {account.get('id', 'unknown')}: {err}")
                result["error_count"] += 1
                result["errors"].append({"account_id": account.get("id", "unknown"), "error": str(err), "record_number": i})
                continue

        conn.commit()
        print(f"\n✅ Updated: {result['success_count']}, ⏭️ Skipped: {result['skipped_count']}, ⚠️ Errors: {result['error_count']}")

    except Exception as err:
        print(f"💥 Unexpected database error: {err}")
        conn.rollback()
    finally:
        if cursor:
            cursor.close()

    return result
