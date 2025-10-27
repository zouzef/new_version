import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common_function import format_date  # make sure this exists

def insert_groups(conn, group_data):
    """
    Insert 'group' records into relation_group_local_session table.
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
        created_records = group_data.get("created", [])
        result["total_processed"] = len(created_records)

        if not created_records:
            print("No group records to insert")
            return result

        print(f"Inserting {len(created_records)} group record(s)...")

        for i, rec in enumerate(created_records, 1):
            try:
                group_id = rec.get("id")
                if not group_id:
                    raise ValueError("Missing required field: id")

                # Check if record exists
                cursor.execute("SELECT id FROM relation_group_local_session WHERE id = %s", (group_id,))
                if cursor.fetchone():
                    print(f"⏭️  Group ID {group_id} already exists — skipping insert.")
                    result["skipped_count"] += 1
                    continue

                # Map fields
                session_id = rec.get("sessionId")
                local_id = rec.get("localId")
                account_id = rec.get("accountId")
                name = rec.get("name", "")
                capacity = rec.get("capacity")
                status = 1 if rec.get("status", True) else 0
                enabled = 1 if rec.get("enabled", True) else 0
                special_group = 1 if rec.get("special_group") else 0 if rec.get("special_group") is not None else None
                access_type = 1 if rec.get("access_type") else 0 if rec.get("access_type") is not None else None
                releaseToken = 1 if rec.get("releaseToken", False) else 0
                useToken = rec.get("useToken")

                created_at = format_date(rec.get("createdAt"))
                updated_at = format_date(rec.get("updatedAt"))
                timestamp = format_date(rec.get("timestamp"))

                cursor.execute("""
                    INSERT INTO relation_group_local_session (
                        id, session_id, local_id, account_id, name, capacity, status, enabled,
                        special_group, access_type, releaseToken, useToken, created_at, updated_at, timestamp
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    group_id, session_id, local_id, account_id, name, capacity, status, enabled,
                    special_group, access_type, releaseToken, useToken,
                    created_at, updated_at, timestamp
                ))

                result["success_count"] += 1
                print(f"✔ Group ID {group_id} inserted successfully")

            except Exception as err:
                print(f"❌ Error inserting Group ID {rec.get('id', 'unknown')}: {err}")
                result["error_count"] += 1
                result["errors"].append({
                    "group_id": rec.get("id", "unknown"),
                    "error": str(err),
                    "record_number": i
                })
                continue

        conn.commit()
        print(f"\n✅ Inserted: {result['success_count']}, Skipped: {result['skipped_count']}, "
              f"Errors: {result['error_count']}, Total: {result['total_processed']}")

    except Exception as err:
        print(f"💥 Database error: {err}")
        conn.rollback()
    finally:
        if cursor:
            cursor.close()

    return result


def update_groups(conn, group_data):
    """
    Update 'group' records in relation_group_local_session table.
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
        updated_records = group_data.get("updated", [])
        result["total_processed"] = len(updated_records)

        if not updated_records:
            print("No group records to update")
            return result

        print(f"🔄 Updating {len(updated_records)} group record(s)...")

        for i, rec in enumerate(updated_records, 1):
            try:
                group_id = rec.get("id")
                if not group_id:
                    raise ValueError("Missing required field: id")

                # Map new data
                new_data = {
                    "session_id": rec.get("sessionId"),
                    "local_id": rec.get("localId"),
                    "account_id": rec.get("accountId"),
                    "name": rec.get("name", ""),
                    "capacity": rec.get("capacity"),
                    "status": 1 if rec.get("status", True) else 0,
                    "enabled": 1 if rec.get("enabled", True) else 0,
                    "special_group": 1 if rec.get("special_group") else 0 if rec.get("special_group") is not None else None,
                    "access_type": 1 if rec.get("access_type") else 0 if rec.get("access_type") is not None else None,
                    "releaseToken": 1 if rec.get("releaseToken", False) else 0,
                    "useToken": rec.get("useToken"),
                    "created_at": format_date(rec.get("createdAt")),
                    "updated_at": format_date(rec.get("updatedAt")),
                    "timestamp": format_date(rec.get("timestamp"))
                }

                # Check existing record
                cursor.execute("SELECT * FROM relation_group_local_session WHERE id = %s", (group_id,))
                existing = cursor.fetchone()

                if not existing:
                    print(f"⚠️  Group ID {group_id} not found — skipping.")
                    result["skipped_count"] += 1
                    continue

                # Compare existing vs new
                identical = True
                for key, value in new_data.items():
                    if str(existing.get(key)) != str(value):
                        identical = False
                        break

                if identical:
                    print(f"⏭️  Group ID {group_id} — no changes detected, skipping.")
                    result["skipped_count"] += 1
                    continue

                # Update record
                cursor.execute("""
                    UPDATE relation_group_local_session SET
                        session_id=%s, local_id=%s, account_id=%s, name=%s, capacity=%s,
                        status=%s, enabled=%s, special_group=%s, access_type=%s,
                        releaseToken=%s, useToken=%s, created_at=%s, updated_at=%s, timestamp=%s, is_sync=1
                    WHERE id=%s
                """, (
                    new_data["session_id"], new_data["local_id"], new_data["account_id"], new_data["name"],
                    new_data["capacity"], new_data["status"], new_data["enabled"], new_data["special_group"],
                    new_data["access_type"], new_data["releaseToken"], new_data["useToken"],
                    new_data["created_at"], new_data["updated_at"], new_data["timestamp"], group_id
                ))

                if cursor.rowcount > 0:
                    result["success_count"] += 1
                    print(f"✔ Group ID {group_id} updated successfully")

            except Exception as err:
                print(f"❌ Error updating Group ID {rec.get('id', 'unknown')}: {err}")
                result["error_count"] += 1
                result["errors"].append({
                    "group_id": rec.get("id", "unknown"),
                    "error": str(err),
                    "record_number": i
                })
                continue

        conn.commit()
        print(f"\n✅ Updated: {result['success_count']}, Skipped: {result['skipped_count']}, "
              f"Errors: {result['error_count']}, Total: {result['total_processed']}")

    except Exception as err:
        print(f"💥 Database error: {err}")
        conn.rollback()
    finally:
        if cursor:
            cursor.close()

    return result
