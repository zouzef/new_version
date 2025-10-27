import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common_function import format_date  # ensure this exists


def insert_cameras(conn, camera_data):
    """
    Insert 'camera' records into the camera table.
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
        created_cameras = camera_data.get("created", [])
        result["total_processed"] = len(created_cameras)

        if not created_cameras:
            print("No camera records to insert")
            return result

        print(f"Inserting {len(created_cameras)} camera record(s)...")

        for i, rec in enumerate(created_cameras, 1):
            try:
                camera_id = rec.get("id")
                if not camera_id:
                    raise ValueError("Missing required field: id")

                # Check if record exists
                cursor.execute("SELECT id FROM camera WHERE id = %s", (camera_id,))
                if cursor.fetchone():
                    print(f"⏭️  Camera ID {camera_id} already exists — skipping insert.")
                    result["skipped_count"] += 1
                    continue

                # Map fields
                slc_id = rec.get("slcId")
                room_id = rec.get("roomId")
                name = rec.get("name", "")
                mac_id = rec.get("mac_id", "")
                username = rec.get("username", "")
                password = rec.get("password", "")
                camera_type = rec.get("type", "webcam")
                status = rec.get("status", "Active")
                enabled = 1 if rec.get("enabled", True) else 0
                timestamp = format_date(rec.get("timestamp"))
                created_at = format_date(rec.get("createdAt"))
                updated_at = format_date(rec.get("updatedAt"))

                cursor.execute("""
                    INSERT INTO camera (
                        id, slc_id, room_id, name, mac_id, username, password,
                        type, status, enabled, timestamp, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    camera_id, slc_id, room_id, name, mac_id, username, password,
                    camera_type, status, enabled, timestamp, created_at, updated_at
                ))

                result["success_count"] += 1
                print(f"✔ Camera ID {camera_id} inserted successfully")

            except Exception as err:
                print(f"❌ Error inserting Camera ID {rec.get('id', 'unknown')}: {err}")
                result["error_count"] += 1
                result["errors"].append({
                    "camera_id": rec.get("id", "unknown"),
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


def update_cameras(conn, camera_data):
    """
    Update 'camera' records in the camera table.
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
        updated_cameras = camera_data.get("updated", [])
        result["total_processed"] = len(updated_cameras)

        if not updated_cameras:
            print("No camera records to update")
            return result

        print(f"🔄 Updating {len(updated_cameras)} camera record(s)...")

        for i, rec in enumerate(updated_cameras, 1):
            try:
                camera_id = rec.get("id")
                if not camera_id:
                    raise ValueError("Missing required field: id")

                # Map new data
                new_data = {
                    "slc_id": rec.get("slcId"),
                    "room_id": rec.get("roomId"),
                    "name": rec.get("name", ""),
                    "mac_id": rec.get("mac_id", ""),
                    "username": rec.get("username", ""),
                    "password": rec.get("password", ""),
                    "type": rec.get("type", "webcam"),
                    "status": rec.get("status", "Active"),
                    "enabled": 1 if rec.get("enabled", True) else 0,
                    "timestamp": format_date(rec.get("timestamp")),
                    "created_at": format_date(rec.get("createdAt")),
                    "updated_at": format_date(rec.get("updatedAt"))
                }

                # Check existing record
                cursor.execute("SELECT * FROM camera WHERE id = %s", (camera_id,))
                existing = cursor.fetchone()

                if not existing:
                    print(f"⚠️  Camera ID {camera_id} not found — skipping.")
                    result["skipped_count"] += 1
                    continue

                # Compare existing vs new data
                identical = True
                for key, value in new_data.items():
                    if str(existing.get(key)) != str(value):
                        identical = False
                        break

                if identical:
                    print(f"⏭️  Camera ID {camera_id} — no changes detected, skipping.")
                    result["skipped_count"] += 1
                    continue

                # Perform update
                cursor.execute("""
                    UPDATE camera SET
                        slc_id=%s, room_id=%s, name=%s, mac_id=%s, username=%s, password=%s,
                        type=%s, status=%s, enabled=%s, timestamp=%s, created_at=%s, updated_at=%s, is_sync=1
                    WHERE id=%s
                """, (
                    new_data["slc_id"], new_data["room_id"], new_data["name"], new_data["mac_id"],
                    new_data["username"], new_data["password"], new_data["type"], new_data["status"],
                    new_data["enabled"], new_data["timestamp"], new_data["created_at"], new_data["updated_at"],
                    camera_id
                ))

                if cursor.rowcount > 0:
                    result["success_count"] += 1
                    print(f"✔ Camera ID {camera_id} updated successfully")

            except Exception as err:
                print(f"❌ Error updating Camera ID {rec.get('id', 'unknown')}: {err}")
                result["error_count"] += 1
                result["errors"].append({
                    "camera_id": rec.get("id", "unknown"),
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
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common_function import format_date  # ensure this exists


def insert_cameras(conn, camera_data):
    """
    Insert 'camera' records into the camera table.
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
        created_cameras = camera_data.get("created", [])
        result["total_processed"] = len(created_cameras)

        if not created_cameras:
            print("No camera records to insert")
            return result

        print(f"Inserting {len(created_cameras)} camera record(s)...")

        for i, rec in enumerate(created_cameras, 1):
            try:
                camera_id = rec.get("id")
                if not camera_id:
                    raise ValueError("Missing required field: id")

                # Check if record exists
                cursor.execute("SELECT id FROM camera WHERE id = %s", (camera_id,))
                if cursor.fetchone():
                    print(f"⏭️  Camera ID {camera_id} already exists — skipping insert.")
                    result["skipped_count"] += 1
                    continue

                # Map fields
                slc_id = rec.get("slcId")
                room_id = rec.get("roomId")
                name = rec.get("name", "")
                mac_id = rec.get("mac_id", "")
                username = rec.get("username", "")
                password = rec.get("password", "")
                camera_type = rec.get("type", "webcam")
                status = rec.get("status", "Active")
                enabled = 1 if rec.get("enabled", True) else 0
                timestamp = format_date(rec.get("timestamp"))
                created_at = format_date(rec.get("createdAt"))
                updated_at = format_date(rec.get("updatedAt"))

                cursor.execute("""
                    INSERT INTO camera (
                        id, slc_id, room_id, name, mac_id, username, password,
                        type, status, enabled, timestamp, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    camera_id, slc_id, room_id, name, mac_id, username, password,
                    camera_type, status, enabled, timestamp, created_at, updated_at
                ))

                result["success_count"] += 1
                print(f"✔ Camera ID {camera_id} inserted successfully")

            except Exception as err:
                print(f"❌ Error inserting Camera ID {rec.get('id', 'unknown')}: {err}")
                result["error_count"] += 1
                result["errors"].append({
                    "camera_id": rec.get("id", "unknown"),
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


def update_cameras(conn, camera_data):
    """
    Update 'camera' records in the camera table.
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
        updated_cameras = camera_data.get("updated", [])
        result["total_processed"] = len(updated_cameras)

        if not updated_cameras:
            print("No camera records to update")
            return result

        print(f"🔄 Updating {len(updated_cameras)} camera record(s)...")

        for i, rec in enumerate(updated_cameras, 1):
            try:
                camera_id = rec.get("id")
                if not camera_id:
                    raise ValueError("Missing required field: id")

                # Map new data
                new_data = {
                    "slc_id": rec.get("slcId"),
                    "room_id": rec.get("roomId"),
                    "name": rec.get("name", ""),
                    "mac_id": rec.get("mac_id", ""),
                    "username": rec.get("username", ""),
                    "password": rec.get("password", ""),
                    "type": rec.get("type", "webcam"),
                    "status": rec.get("status", "Active"),
                    "enabled": 1 if rec.get("enabled", True) else 0,
                    "timestamp": format_date(rec.get("timestamp")),
                    "created_at": format_date(rec.get("createdAt")),
                    "updated_at": format_date(rec.get("updatedAt"))
                }

                # Check existing record
                cursor.execute("SELECT * FROM camera WHERE id = %s", (camera_id,))
                existing = cursor.fetchone()

                if not existing:
                    print(f"⚠️  Camera ID {camera_id} not found — skipping.")
                    result["skipped_count"] += 1
                    continue

                # Compare existing vs new data
                identical = True
                for key, value in new_data.items():
                    if str(existing.get(key)) != str(value):
                        identical = False
                        break

                if identical:
                    print(f"⏭️  Camera ID {camera_id} — no changes detected, skipping.")
                    result["skipped_count"] += 1
                    continue

                # Perform update
                cursor.execute("""
                    UPDATE camera SET
                        slc_id=%s, room_id=%s, name=%s, mac_id=%s, username=%s, password=%s,
                        type=%s, status=%s, enabled=%s, timestamp=%s, created_at=%s, updated_at=%s, is_sync=1
                    WHERE id=%s
                """, (
                    new_data["slc_id"], new_data["room_id"], new_data["name"], new_data["mac_id"],
                    new_data["username"], new_data["password"], new_data["type"], new_data["status"],
                    new_data["enabled"], new_data["timestamp"], new_data["created_at"], new_data["updated_at"],
                    camera_id
                ))

                if cursor.rowcount > 0:
                    result["success_count"] += 1
                    print(f"✔ Camera ID {camera_id} updated successfully")

            except Exception as err:
                print(f"❌ Error updating Camera ID {rec.get('id', 'unknown')}: {err}")
                result["error_count"] += 1
                result["errors"].append({
                    "camera_id": rec.get("id", "unknown"),
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
