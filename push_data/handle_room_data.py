import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common_function import format_date

def insert_room_data(conn, local_with_room_data):
    """
    Push local + room data from API.
    - Inserts only if ID doesn't exist
    - Skips if record already exists
    """
    result = {
        "local_success_count": 0,
        "room_success_count": 0,
        "error_count": 0,
        "skipped_count": 0,
        "errors": [],
        "total_locals_processed": 0,
        "total_rooms_processed": 0
    }

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)

        all_locals = local_with_room_data.get("created", []) + local_with_room_data.get("updated", [])
        result["total_locals_processed"] = len(all_locals)
        print(f"Processing {len(all_locals)} local record(s)...")

        for i, local in enumerate(all_locals, 1):
            try:
                local_id = local.get("id")
                if not local_id:
                    raise ValueError("Missing required field: id")

                # Check if local already exists
                cursor.execute("SELECT * FROM local WHERE id = %s", (local_id,))
                existing_local = cursor.fetchone()
                if existing_local:
                    print(f"⏭️ Local ID {local_id} already exists — skipping insert.")
                    result["skipped_count"] += 1
                    continue

                # Prepare local fields
                account_id = local.get("accountId")
                name = local.get("name", "")
                address = local.get("address", "")
                gps = local.get("gps", "")
                status = 1 if local.get("status", True) else 0
                enabled = 1 if local.get("enabled", True) else 0
                default_local = 1 if local.get("default", False) else 0
                created_at = format_date(local.get("createdAt"))
                updated_at = format_date(local.get("updatedAt"))

                # Insert local
                cursor.execute("""
                    INSERT INTO local (id, account_id, name, address, gps, status, enabled, default_local, created_at, updated_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (local_id, account_id, name, address, gps, status, enabled, default_local, created_at, updated_at))
                result["local_success_count"] += 1
                print(f"✔ Local ID {local_id} inserted successfully")

                # Process rooms
                rooms = local.get("rooms", [])
                result["total_rooms_processed"] += len(rooms)
                for room in rooms:
                    try:
                        room_id = room.get("id")
                        if not room_id:
                            continue

                        cursor.execute("SELECT * FROM room WHERE id = %s", (room_id,))
                        if cursor.fetchone():
                            print(f"⏭️ Room ID {room_id} already exists — skipping insert.")
                            result["skipped_count"] += 1
                            continue

                        room_local_id = room.get("localId")
                        room_name = room.get("name", "")
                        capacity = room.get("capacity", "")
                        created_at = format_date(room.get("createdAt"))
                        updated_at = format_date(room.get("updatedAt"))

                        cursor.execute("""
                            INSERT INTO room (id, local_id, name, capacity, created_at, updated_at)
                            VALUES (%s,%s,%s,%s,%s,%s)
                        """, (room_id, room_local_id, room_name, capacity, created_at, updated_at))
                        result["room_success_count"] += 1
                        print(f"✔ Room ID {room_id} inserted successfully")
                    except Exception as err:
                        result["error_count"] += 1
                        result["errors"].append({"room_id": room.get("id", None), "local_id": local_id, "error": str(err)})
                        print(f"❌ Error inserting room: {err}")

            except Exception as err:
                result["error_count"] += 1
                result["errors"].append({"local_id": local.get("id", None), "error": str(err)})
                print(f"❌ Error inserting local: {err}")

        conn.commit()
    finally:
        if cursor:
            cursor.close()

    return result



def update_room_data(conn, local_with_room_data):
    """
    Update local + room data
    - Skips update if data is identical
    """
    result = {
        "local_success_count": 0,
        "room_success_count": 0,
        "error_count": 0,
        "skipped_count": 0,
        "errors": [],
        "total_locals_processed": 0,
        "total_rooms_processed": 0
    }

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        updated_locals = local_with_room_data.get("updated", [])
        result["total_locals_processed"] = len(updated_locals)

        if not updated_locals:
            print("No local records to update")
            return result

        for i, local in enumerate(updated_locals, 1):
            try:
                local_id = local.get("id")
                if not local_id:
                    raise ValueError("Missing required field: id")

                # New data dict
                new_local_data = {
                    "account_id": local.get("accountId"),
                    "name": local.get("name", ""),
                    "address": local.get("address", ""),
                    "gps": local.get("gps", ""),
                    "status": 1 if local.get("status", True) else 0,
                    "enabled": 1 if local.get("enabled", True) else 0,
                    "default_local": 1 if local.get("default", False) else 0,
                    "updated_at": format_date(local.get("updatedAt"))
                }

                # Fetch existing record
                cursor.execute("SELECT * FROM local WHERE id = %s", (local_id,))
                existing_local = cursor.fetchone()
                if not existing_local:
                    print(f"⚠️ Local ID {local_id} not found — skipping update.")
                    continue

                # Compare data
                same_data = all(str(existing_local.get(k)) == str(v) for k, v in new_local_data.items())
                if same_data:
                    result["skipped_count"] += 1
                    print(f"⏭️ Local ID {local_id} — no changes detected (skipped).")
                    continue

                # Update only if different
                cursor.execute("""
                    UPDATE local SET
                        account_id=%s, name=%s, address=%s, gps=%s,
                        status=%s, enabled=%s, default_local=%s, updated_at=%s
                    WHERE id=%s
                """, (*new_local_data.values(), local_id))
                result["local_success_count"] += 1
                print(f"✔ Local ID {local_id} updated successfully")

                # Process rooms
                rooms = local.get("rooms", [])
                result["total_rooms_processed"] += len(rooms)
                for room in rooms:
                    try:
                        room_id = room.get("id")
                        if not room_id:
                            continue

                        new_room_data = {
                            "local_id": room.get("localId"),
                            "name": room.get("name", ""),
                            "capacity": room.get("capacity", ""),
                            "updated_at": format_date(room.get("updatedAt"))
                        }

                        cursor.execute("SELECT * FROM room WHERE id = %s", (room_id,))
                        existing_room = cursor.fetchone()
                        if not existing_room:
                            print(f"⚠️ Room ID {room_id} not found — skipping update.")
                            continue

                        same_data = all(str(existing_room.get(k)) == str(v) for k, v in new_room_data.items())
                        if same_data:
                            result["skipped_count"] += 1
                            print(f"⏭️ Room ID {room_id} — no changes detected (skipped).")
                            continue

                        cursor.execute("""
                            UPDATE room SET local_id=%s, name=%s, capacity=%s, updated_at=%s
                            WHERE id=%s
                        """, (*new_room_data.values(), room_id))
                        result["room_success_count"] += 1
                        print(f"✔ Room ID {room_id} updated successfully")

                    except Exception as err:
                        result["error_count"] += 1
                        result["errors"].append({"room_id": room.get("id", None), "local_id": local_id, "error": str(err)})
                        print(f"❌ Error updating room: {err}")

            except Exception as err:
                result["error_count"] += 1
                result["errors"].append({"local_id": local.get("id", None), "error": str(err)})
                print(f"❌ Error updating local: {err}")

        conn.commit()
    finally:
        if cursor:
            cursor.close()

    return result