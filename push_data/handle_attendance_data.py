import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common_function import format_date  # Ensure this exists


def insert_attendance(conn, attendance_data):
    """
    Insert attendance records into the 'attendance' table.
    - Skips insert if ID already exists locally.
    """
    result = {"success_count":0, "skipped_count":0, "error_count":0, "errors":[], "total_processed":0}
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        created_attendance = attendance_data.get("created", []) or []
        result["total_processed"] = len(created_attendance)

        if not created_attendance:
            print("No attendance records to insert")
            return result

        print(f"Processing {len(created_attendance)} attendance record(s)...")

        for i, rec in enumerate(created_attendance, 1):
            try:
                attendance_id = rec.get("id")
                if not attendance_id:
                    raise ValueError("Missing required field: id")

                # Skip if attendance already exists
                # cursor.execute("SELECT id FROM attendance WHERE id=%s", (attendance_id,))
                # if cursor.fetchone():
                #     print(f"⏭️ Attendance ID {attendance_id} already exists — skipping insert.")
                #     result["skipped_count"] += 1
                #     continue

                # Map fields safely
                data = {
                    "user_id": rec.get("userId"),
                    "account_id": rec.get("accountId"),
                    "calander_id": rec.get("calenderId"),
                    "session_id": rec.get("sessionId"),
                    "group_session_id": rec.get("groupId"),
                    "is_present": 1 if rec.get("present", False) else 0,
                    "day": format_date(rec.get("day")),
                    "note": rec.get("note"),
                    "is_editable": 1 if rec.get("editable", True) else 0,
                    "enabled": 1 if rec.get("enabled", True) else 0,
                    "releaseToken": 1 if rec.get("releaseToken", False) else 0,
                    "useToken": rec.get("useToken"),
                    "created_at": format_date(rec.get("createdAt")),
                    "updated_at": format_date(rec.get("updatedAt")),
                    "timestamp": format_date(rec.get("timestamp")),
                    "slc_edit":0
                }

                cursor.execute("""
                    INSERT INTO attendance (
                        id, user_id, account_id, session_id, group_session_id, is_present,
                        day, note, is_editable, enabled, created_at, updated_at,
                        timestamp, releaseToken, useToken,calander_id,slc_edit
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0)
                """, (
                    attendance_id, data["user_id"], data["account_id"], data["session_id"],
                    data["group_session_id"], data["is_present"], data["day"], data["note"],
                    data["is_editable"], data["enabled"], data["created_at"], data["updated_at"],
                    data["timestamp"], data["releaseToken"], data["useToken"],data["calander_id"]
                ))

                result["success_count"] += 1
                print(f"✔ Attendance ID {attendance_id} inserted successfully")

            except Exception as e:
                print(f"❌ Error inserting attendance ID {rec.get('id', 'unknown')}: {e}")
                result["error_count"] += 1
                result["errors"].append({"attendance_id": rec.get("id", "unknown"), "error": str(e), "record_number": i})
                continue

        conn.commit()
        print(f"\n✅ Inserted: {result['success_count']}, Skipped: {result['skipped_count']}, Errors: {result['error_count']}")

    except Exception as e:
        print(f"💥 Database error: {e}")
        conn.rollback()
    finally:
        if cursor:
            cursor.close()
    return result


def update_attendance_data(conn, attendance_data, mac_address=None):
    """
    Update attendance records in the 'attendance' table.
    - Skips update if data is identical to existing row
    - Checks releaseToken logic if provided
    """
    result = {"success_count":0, "skipped_count":0, "error_count":0, "errors":[], "total_processed":0}
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        updated_attendance = attendance_data.get("updated", []) or []
        result["total_processed"] = len(updated_attendance)

        if not updated_attendance:
            print("No attendance records to update")
            return result

        print(f"🔄 Updating {len(updated_attendance)} attendance record(s)...")

        for i, rec in enumerate(updated_attendance, 1):
            try:
                attendance_id = rec.get("id")
                if not attendance_id:
                    raise ValueError("Missing required field: id")

                # Map new data
                new_data = {
                    "user_id": rec.get("userId"),
                    "account_id": rec.get("accountId"),
                    "session_id": rec.get("sessionId"),
                    "group_session_id": rec.get("groupId"),
                    "is_present": 1 if rec.get("present", False) else 0,
                    "day": format_date(rec.get("day")),
                    "note": rec.get("note"),
                    "is_editable": 1 if rec.get("editable", True) else 0,
                    "enabled": 1 if rec.get("enabled", True) else 0,
                    "releaseToken": rec.get("releaseToken"),
                    "useToken": rec.get("useToken"),
                    "updated_at": format_date(rec.get("updatedAt")),
                    "timestamp": format_date(rec.get("timestamp"))
                }

                # Special releaseToken logic
                if new_data["releaseToken"] and mac_address and new_data["useToken"] == mac_address:
                    print(f"⚠️ Cannot update Attendance ID {attendance_id}: releaseToken active on this machine")
                    continue

                # Check existing row
                cursor.execute("SELECT * FROM attendance WHERE id=%s", (attendance_id,))
                existing = cursor.fetchone()
                if not existing:
                    print(f"⚠️ Attendance ID {attendance_id} not found — skipping update.")
                    result["skipped_count"] += 1
                    continue

                # Compare existing vs new data
                same_data = True
                for key, value in new_data.items():
                    old_val = str(existing.get(key)) if existing.get(key) is not None else None
                    new_val = str(value) if value is not None else None
                    if old_val != new_val:
                        same_data = False
                        break

                if same_data:
                    result["skipped_count"] += 1
                    print(f"⏭️ Attendance ID {attendance_id} — no changes detected (skipped).")
                    continue

                # Update only if different
                cursor.execute("""
                    UPDATE attendance SET
                        user_id=%s, account_id=%s, session_id=%s, group_session_id=%s,
                        is_present=%s, day=%s, note=%s, is_editable=%s, enabled=%s,
                        updated_at=%s, timestamp=%s
                    WHERE id=%s
                """, (
                    new_data["user_id"], new_data["account_id"], new_data["session_id"],
                    new_data["group_session_id"], new_data["is_present"], new_data["day"],
                    new_data["note"], new_data["is_editable"], new_data["enabled"],
                    new_data["updated_at"], new_data["timestamp"], attendance_id
                ))

                result["success_count"] += 1
                print(f"✔ Attendance ID {attendance_id} updated successfully")

            except Exception as e:
                print(f"❌ Error updating attendance ID {rec.get('id', 'unknown')}: {e}")
                result["error_count"] += 1
                result["errors"].append({"attendance_id": rec.get("id", "unknown"), "error": str(e), "record_number": i})
                continue

        conn.commit()
        print(f"\n✅ Updated: {result['success_count']}, Skipped: {result['skipped_count']}, Errors: {result['error_count']}")

    except Exception as e:
        print(f"💥 Database error: {e}")
        conn.rollback()
    finally:
        if cursor:
            cursor.close()
    return result
