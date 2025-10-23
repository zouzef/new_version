import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common_function import format_date



def push_tablet_data(conn, tablet_data):
    """
    Push 'slcTablet' data into the MariaDB tablet table.
    Inserts only if tablet ID does not exist. Skips if exists.
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
        updated_tablets = tablet_data.get("updated", [])
        all_tablets = created_tablets + updated_tablets
        result["total_processed"] = len(all_tablets)

        if result["total_processed"] == 0:
            print("No tablet records to process")
            return result

        print(f"Processing {len(all_tablets)} tablet(s)...")

        for i, tablet in enumerate(all_tablets, 1):
            try:
                tablet_id = tablet.get("id")
                if not tablet_id:
                    raise ValueError("Missing required field: id")

                # Check if tablet already exists
                cursor.execute("SELECT id FROM tablet WHERE id = %s", (tablet_id,))
                if cursor.fetchone():
                    print(f"⏭️  Tablet ID {tablet_id} already exists — skipping insert.")
                    result["skipped_count"] += 1
                    continue

                # Extract fields
                slc_id = tablet.get("slcId")
                room_id = tablet.get("roomId")
                name = tablet.get("name", "")
                mac_id = tablet.get("mac_id", "")
                password = tablet.get("password", "")
                status = tablet.get("status", "Active")
                enabled = 1 if tablet.get("enabled", True) else 0
                timestamp_val = format_date(tablet.get("timestamp"))
                created_at = format_date(tablet.get("createdAt"))
                updated_at = format_date(tablet.get("updatedAt"))

                # Insert
                cursor.execute("""
                    INSERT INTO tablet (
                        id, slc_id, room_id, name, mac_id, password, status, enabled,
                        timestamp, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    tablet_id, slc_id, room_id, name, mac_id, password,
                    status, enabled, timestamp_val, created_at, updated_at
                ))

                result["success_count"] += 1
                print(f"✔ Tablet ID {tablet_id} inserted successfully")

            except Exception as err:
                result["error_count"] += 1
                result["errors"].append({
                    "tablet_id": tablet.get("id", "unknown"),
                    "error": str(err),
                    "record_number": i
                })
                print(f"❌ Error inserting Tablet ID {tablet.get('id', 'unknown')}: {err}")
                continue

        conn.commit()
        print(f"\n✅ Inserted: {result['success_count']}")
        print(f"⏭️  Skipped (already exist): {result['skipped_count']}")
        print(f"⚠️  Errors: {result['error_count']}")
        print(f"🧮 Total processed: {result['total_processed']}")

    except Exception as err:
        print(f"💥 Unexpected database error: {err}")
        conn.rollback()
    finally:
        if cursor:
            cursor.close()

    return result


def update_tablet(conn, tablet_data):
    """
    Update 'slcTablet' data in the MariaDB tablet table.
    Only updates if data has changed; skips otherwise.
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

        if result["total_processed"] == 0:
            print("No tablet records to update")
            return result

        print(f"Updating {len(updated_tablets)} tablet record(s)...")

        for i, tablet in enumerate(updated_tablets, 1):
            try:
                tablet_id = tablet.get("id")
                if not tablet_id:
                    raise ValueError("Missing required field: id")

                # Extract new data
                new_data = {
                    "slc_id": tablet.get("slcId"),
                    "room_id": tablet.get("roomId"),
                    "name": tablet.get("name"),
                    "mac_id": tablet.get("mac_id"),
                    "password": tablet.get("password"),
                    "status": tablet.get("status"),
                    "enabled": 1 if tablet.get("enabled", True) else 0,
                    "timestamp": format_date(tablet.get("timestamp")),
                    "created_at": format_date(tablet.get("createdAt")),
                    "updated_at": format_date(tablet.get("updatedAt"))
                }

                # Step 1: Check if tablet exists
                cursor.execute("SELECT * FROM tablet WHERE id = %s", (tablet_id,))
                existing = cursor.fetchone()
                if not existing:
                    print(f"⚠️  Tablet ID {tablet_id} not found — skipping.")
                    continue

                # Step 2: Compare data
                same_data = True
                for key, value in new_data.items():
                    old_val = str(existing.get(key)) if existing.get(key) is not None else None
                    new_val = str(value) if value is not None else None
                    if old_val != new_val:
                        same_data = False
                        break

                if same_data:
                    result["skipped_count"] += 1
                    print(f"⏭️  Tablet ID {tablet_id} — no changes detected (skipped).")
                    continue

                # Step 3: Update only if different
                cursor.execute("""
                    UPDATE tablet SET
                        slc_id=%s, room_id=%s, name=%s, mac_id=%s, password=%s,
                        status=%s, enabled=%s, timestamp=%s, created_at=%s, updated_at=%s
                    WHERE id=%s
                """, (
                    new_data["slc_id"], new_data["room_id"], new_data["name"], new_data["mac_id"],
                    new_data["password"], new_data["status"], new_data["enabled"],
                    new_data["timestamp"], new_data["created_at"], new_data["updated_at"],
                    tablet_id
                ))

                if cursor.rowcount > 0:
                    result["success_count"] += 1
                    print(f"✔ Tablet ID {tablet_id} updated successfully")
                else:
                    print(f"⚠️  Tablet ID {tablet_id} update query executed, but no changes detected")

            except Exception as err:
                result["error_count"] += 1
                result["errors"].append({
                    "tablet_id": tablet.get("id", "unknown"),
                    "error": str(err),
                    "record_number": i
                })
                print(f"❌ Error updating Tablet ID {tablet.get('id', 'unknown')}: {err}")
                continue

        conn.commit()
        print(f"\n✅ Updated: {result['success_count']}")
        print(f"⏭️  Skipped (no change): {result['skipped_count']}")
        print(f"⚠️  Errors: {result['error_count']}")
        print(f"🧮 Total processed: {result['total_processed']}")

    except Exception as err:
        print(f"💥 Unexpected database error: {err}")
        conn.rollback()
    finally:
        if cursor:
            cursor.close()

    return result