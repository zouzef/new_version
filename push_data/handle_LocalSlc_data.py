
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common_function import format_date  # make sure you have format_date in common_function.py


def insert_slc_local(conn, slc_local_data):
    """
    Insert 'slc_local' records into slc_local table.
    - Skips insert if ID already exists.
    """
    result = {
        "success_count": 0,
        "skipped_count": 0,
        "error_count": 0,
        "errors": [],
        "total_processed": 0
    }

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        created_records = slc_local_data.get("created", [])
        result["total_processed"] = len(created_records)

        if not created_records:
            print("No slc_local records to insert")
            return result

        print(f"Inserting {len(created_records)} slc_local record(s)...")

        for i, rec in enumerate(created_records, 1):
            try:
                rec_id = rec.get("id")
                if not rec_id:
                    raise ValueError("Missing required field: id")

                # Check if record exists
                cursor.execute("SELECT id FROM slc_local WHERE id = %s", (rec_id,))
                if cursor.fetchone():
                    print(f"⏭️  slc_local ID {rec_id} already exists — skipping insert.")
                    result["skipped_count"] += 1
                    continue

                # Map fields
                slc_id = rec.get("slcId")
                account_id = rec.get("accountId")
                local_id = rec.get("localId")
                enabled = 1 if rec.get("enabled") else 0
                timestamp = format_date(rec.get("timestamp"))
                created_at = format_date(rec.get("createdAt"))
                updated_at = format_date(rec.get("updatedAt"))

                cursor.execute("""
                    INSERT INTO slc_local (
                        id, slc_id, account_id, local_id, enabled, timestamp, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (rec_id, slc_id, account_id, local_id, enabled, timestamp, created_at, updated_at))

                result["success_count"] += 1
                print(f"✔ slc_local ID {rec_id} inserted successfully")

            except Exception as err:
                print(f"❌ Error inserting slc_local ID {rec.get('id', 'unknown')}: {err}")
                result["error_count"] += 1
                result["errors"].append({"slc_local_id": rec.get("id", "unknown"), "error": str(err), "record_number": i})
                continue

        conn.commit()
        print(f"\n✅ Inserted: {result['success_count']}, Skipped: {result['skipped_count']}, Errors: {result['error_count']}, Total: {result['total_processed']}")

    except Exception as err:
        print(f"💥 Database error: {err}")
        conn.rollback()
    finally:
        if cursor:
            cursor.close()

    return result


def update_slc_local(conn, slc_local_data):
    """
    Update 'slc_local' records in slc_local table.
    - Skips update if data is identical.
    - Prints warning if ID not found.
    """
    result = {
        "success_count": 0,
        "skipped_count": 0,
        "error_count": 0,
        "errors": [],
        "total_processed": 0
    }

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        updated_records = slc_local_data.get("updated", [])
        result["total_processed"] = len(updated_records)

        if not updated_records:
            print("No slc_local records to update")
            return result

        print(f"🔄 Updating {len(updated_records)} slc_local record(s)...")

        for i, rec in enumerate(updated_records, 1):
            try:
                rec_id = rec.get("id")
                if not rec_id:
                    raise ValueError("Missing required field: id")

                # Map new data
                new_data = {
                    "slc_id": rec.get("slcId"),
                    "account_id": rec.get("accountId"),
                    "local_id": rec.get("localId"),
                    "enabled": 1 if rec.get("enabled") else 0,
                    "timestamp": format_date(rec.get("timestamp")),
                    "created_at": format_date(rec.get("createdAt")),
                    "updated_at": format_date(rec.get("updatedAt"))
                }

                # Check existing record
                cursor.execute("SELECT * FROM slc_local WHERE id = %s", (rec_id,))
                existing = cursor.fetchone()

                if not existing:
                    print(f"⚠️  slc_local ID {rec_id} not found — skipping.")
                    result["skipped_count"] += 1
                    continue

                # Compare existing with new data
                identical = True
                for key, value in new_data.items():
                    old_val = existing.get(key)
                    new_val = value
                    if str(old_val) != str(new_val):
                        identical = False
                        break

                if identical:
                    print(f"⏭️  slc_local ID {rec_id} — no changes detected, skipping.")
                    result["skipped_count"] += 1
                    continue

                # Update only if different
                cursor.execute("""
                    UPDATE slc_local SET
                        slc_id=%s, account_id=%s, local_id=%s, enabled=%s,
                        timestamp=%s, created_at=%s, updated_at=%s
                    WHERE id=%s
                """, (new_data["slc_id"], new_data["account_id"], new_data["local_id"], new_data["enabled"],
                      new_data["timestamp"], new_data["created_at"], new_data["updated_at"], rec_id))

                if cursor.rowcount > 0:
                    result["success_count"] += 1
                    print(f"✔ slc_local ID {rec_id} updated successfully")

            except Exception as err:
                print(f"❌ Error updating slc_local ID {rec.get('id', 'unknown')}: {err}")
                result["error_count"] += 1
                result["errors"].append({"slc_local_id": rec.get("id", "unknown"), "error": str(err), "record_number": i})
                continue

        conn.commit()
        print(f"\n✅ Updated: {result['success_count']}, Skipped: {result['skipped_count']}, Errors: {result['error_count']}, Total: {result['total_processed']}")

    except Exception as err:
        print(f"💥 Database error: {err}")
        conn.rollback()
    finally:
        if cursor:
            cursor.close()

    return result
