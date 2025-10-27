import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common_function import format_date  # ensure this exists


def insert_tablets(conn, tablet_data):
    """
    Insert 'tablet' records into the tablet table.
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
        created_tablets = tablet_data.get("created", [])
        result["total_processed"] = len(created_tablets)

        if not created_tablets:
            print("No tablet records to insert")
            return result

        print(f"Inserting {len(created_tablets)} tablet record(s)...")

        for i, rec in enumerate(created_tablets, 1):
            try:
                tablet_id = rec.get("id")
                if not tablet_id:
                    raise ValueError("Missing required field: id")

                # Check if record exists
                cursor.execute("SELECT id FROM tablet WHERE id = %s", (tablet_id,))
                if cursor.fetchone():
                    print(f"⏭️  Tablet ID {tablet_id} already exists — skipping insert.")
                    result["skipped_count"] += 1
                    continue

                # Map fields
                slc_id = rec.get("slcId")
                room_id = rec.get("roomId")
                name = rec.get("name", "")
                mac_id = rec.get("mac_id", "")
                password = rec.get("password", "")
                status = rec.get("status", "Active")
                enabled = 1 if rec.get("enabled", True) else 0
                timestamp = format_date(rec.get("timestamp"))
                created_at = format_date(rec.get("createdAt"))
                updated_at = format_date(rec.get("updatedAt"))

                cursor.execute("""
                    INSERT INTO tablet (
                        id, slc_id, room_id, name, mac_id, password,
                        status, enabled, timestamp, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    tablet_id, slc_id, room_id, name, mac_id, password,
                    status, enabled, timestamp, created_at, updated_at
                ))

                result["success_count"] += 1
                print(f"✔ Tablet ID {tablet_id} inserted successfully")

            except Exception as err:
                print(f"❌ Error inserting Tablet ID {rec.get('id', 'unknown')}: {err}")
                result["error_count"] += 1
                result["errors"].append({
                    "tablet_id": rec.get("id", "unknown"),
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



def update_tablets(conn, tablet_data):
    """
    Update 'tablet' records in the tablet table.
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
        updated_tablets = tablet_data.get("updated", [])
        result["total_processed"] = len(updated_tablets)

        if not updated_tablets:
            print("No tablet records to update")
            return result

        print(f"🔄 Updating {len(updated_tablets)} tablet record(s)...")

        for i, rec in enumerate(updated_tablets, 1):
            try:
                tablet_id = rec.get("id")
                if not tablet_id:
                    raise ValueError("Missing required field: id")

                # Map new data
                new_data = {
                    "slc_id": rec.get("slcId"),
                    "room_id": rec.get("roomId"),
                    "name": rec.get("name", ""),
                    "mac_id": rec.get("mac_id", ""),
                    "password": rec.get("password", ""),
                    "status": rec.get("status", "Active"),
                    "enabled": 1 if rec.get("enabled", True) else 0,
                    "timestamp": format_date(rec.get("timestamp")),
                    "created_at": format_date(rec.get("createdAt")),
                    "updated_at": format_date(rec.get("updatedAt"))
                }

                # Check existing record
                cursor.execute("SELECT * FROM tablet WHERE id = %s", (tablet_id,))
                existing = cursor.fetchone()

                if not existing:
                    print(f"⚠️  Tablet ID {tablet_id} not found — skipping.")
                    result["skipped_count"] += 1
                    continue

                # Compare existing vs new data
                identical = True
                for key, value in new_data.items():
                    if str(existing.get(key)) != str(value):
                        identical = False
                        break

                if identical:
                    print(f"⏭️  Tablet ID {tablet_id} — no changes detected, skipping.")
                    result["skipped_count"] += 1
                    continue

                # Perform update
                cursor.execute("""
                    UPDATE tablet SET
                        slc_id=%s, room_id=%s, name=%s, mac_id=%s, password=%s,
                        status=%s, enabled=%s, timestamp=%s, created_at=%s, updated_at=%s, is_sync=1
                    WHERE id=%s
                """, (
                    new_data["slc_id"], new_data["room_id"], new_data["name"],
                    new_data["mac_id"], new_data["password"], new_data["status"],
                    new_data["enabled"], new_data["timestamp"],
                    new_data["created_at"], new_data["updated_at"], tablet_id
                ))

                if cursor.rowcount > 0:
                    result["success_count"] += 1
                    print(f"✔ Tablet ID {tablet_id} updated successfully")

            except Exception as err:
                print(f"❌ Error updating Tablet ID {rec.get('id', 'unknown')}: {err}")
                result["error_count"] += 1
                result["errors"].append({
                    "tablet_id": rec.get("id", "unknown"),
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
