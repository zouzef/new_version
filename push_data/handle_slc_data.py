import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common_function import format_date

def insert_slc_data(conn, slc_data):
    """
    Insert 'slc_local' data into the MariaDB slc table.
    - Inserts only new records.
    - Skips if record ID already exists.
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
        created_slc = slc_data.get("created", [])
        result["total_processed"] = len(created_slc)

        print(f"Processing {len(created_slc)} new SLC record(s)...")

        for i, slc in enumerate(created_slc, 1):
            try:
                slc_id = slc.get("id")
                if not slc_id:
                    raise ValueError("Missing required field: id")

                # Check if already exists
                cursor.execute("SELECT id FROM slc WHERE id = %s", (slc_id,))
                if cursor.fetchone():
                    print(f"⏭️ SLC ID {slc_id} already exists — skipping insert.")
                    result["skipped_count"] += 1
                    continue

                # Map fields
                uuid = slc.get("uuid")
                username = slc.get("username")
                slc_username = slc.get("slc_username")
                slc_password = slc.get("slc_password")
                timestamp = slc.get("timestamp")
                created_at = slc.get("createdAt")
                updated_at = slc.get("updatedAt")

                print(f"Inserting SLC {i}/{len(created_slc)} - ID {slc_id}")

                cursor.execute("""
                    INSERT INTO slc (
                        id, uuid, username, slc_username, slc_password,
                        timestamp, created_at, updated_at
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (slc_id, uuid, username, slc_username, slc_password,
                      timestamp, created_at, updated_at))

                result["success_count"] += 1
                print(f"✔ SLC ID {slc_id} inserted successfully")

            except Exception as err:
                error_msg = f"❌ Error inserting SLC ID {slc.get('id', 'unknown')}: {err}"
                print(error_msg)
                result["error_count"] += 1
                result["errors"].append({"slc_id": slc.get("id", "unknown"), "error": str(err), "record_number": i})
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


def updated_slc_data(conn, slc_data):
    """
    Update 'slc_local' data in MariaDB.
    - Skips update if data is identical.
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
        updated_slc = slc_data.get("updated", [])
        result["total_processed"] = len(updated_slc)

        if not updated_slc:
            print("No SLC records to update")
            return result

        print(f"Updating {len(updated_slc)} SLC record(s)...")

        for i, slc in enumerate(updated_slc, 1):
            try:
                slc_id = slc.get("id")
                if not slc_id:
                    raise ValueError("Missing required field: id")

                # New data mapping
                new_data = {
                    "uuid": slc.get("uuid"),
                    "username": slc.get("username"),
                    "slc_username": slc.get("slc_username"),
                    "slc_password": slc.get("slc_password"),
                    "timestamp": slc.get("timestamp"),
                    "created_at": slc.get("createdAt"),
                    "updated_at": slc.get("updatedAt")
                }

                # Fetch existing data
                cursor.execute("SELECT * FROM slc WHERE id = %s", (slc_id,))
                existing = cursor.fetchone()
                if not existing:
                    print(f"⚠️ SLC ID {slc_id} not found — skipping update")
                    continue

                # Compare fields
                identical = True
                for key, value in new_data.items():
                    old_value = str(existing.get(key)) if existing.get(key) is not None else None
                    new_value = str(value) if value is not None else None
                    if old_value != new_value:
                        identical = False
                        break

                if identical:
                    print(f"⏭️ SLC ID {slc_id} — no changes detected (skipped)")
                    result["skipped_count"] += 1
                    continue

                # Update only if different
                cursor.execute("""
                    UPDATE slc SET
                        uuid=%s, username=%s, slc_username=%s, slc_password=%s,
                        timestamp=%s, created_at=%s, updated_at=%s
                    WHERE id=%s
                """, (
                    new_data["uuid"], new_data["username"], new_data["slc_username"], new_data["slc_password"],
                    new_data["timestamp"], new_data["created_at"], new_data["updated_at"], slc_id
                ))

                result["success_count"] += 1
                print(f"✔ SLC ID {slc_id} updated successfully")

            except Exception as err:
                error_msg = f"❌ Error updating SLC ID {slc.get('id', 'unknown')}: {err}"
                print(error_msg)
                result["error_count"] += 1
                result["errors"].append({"slc_id": slc.get("id", "unknown"), "error": str(err), "record_number": i})
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