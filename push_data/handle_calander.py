import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common_function import format_date

def insert_calendar_data(conn, calendar_data):
    """
    Insert 'relation_calander_group_session' data into MariaDB.
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
        created_calendar = calendar_data.get("created", [])
        result["total_processed"] = len(created_calendar)

        print(f"Processing {len(created_calendar)} new calendar record(s)...")

        for i, cal in enumerate(created_calendar, 1):
            try:
                cal_id = cal.get("id")
                if not cal_id:
                    raise ValueError("Missing required field: id")

                # Check if already exists
                cursor.execute("SELECT id FROM relation_calander_group_session WHERE id = %s", (cal_id,))
                if cursor.fetchone():
                    print(f"⏭️ Calendar ID {cal_id} already exists — skipping insert.")
                    result["skipped_count"] += 1
                    continue

                # Map fields
                session_id = cal.get("sessionId")
                account_id = cal.get("accountId")
                local_id = cal.get("localId")
                group_session_id = cal.get("groupId")
                room_id = cal.get("roomId")
                teacher_id = cal.get("teacherId")
                subject_id = cal.get("subjectId")
                color = cal.get("color")
                status = 1 if cal.get("status", True) else 0
                description = cal.get("description")
                start_time = format_date(cal.get("start_time"))
                end_time = format_date(cal.get("end_time"))
                ref = cal.get("ref")
                date = format_date(cal.get("date"))
                refresh = 1 if cal.get("refresh", False) else 0
                title = cal.get("title", "")
                enabled = 1 if cal.get("enabled", True) else 0
                type_val = cal.get("type")
                teacher_present = 1 if cal.get("teacher_present", False) else 0
                force_teacher_present = 1 if cal.get("force_teacher_present", False) else 0
                created_at = format_date(cal.get("createdAt"))
                updated_at = format_date(cal.get("updatedAt"))
                timestamp = format_date(cal.get("timestamp"))
                releaseToken = 1 if cal.get("releaseToken", False) else 0
                useToken = cal.get("useToken")

                print(f"Inserting Calendar {i}/{len(created_calendar)} - ID {cal_id}")

                cursor.execute("""
                    INSERT INTO relation_calander_group_session (
                        id, session_id, account_id, local_id, group_session_id, room_id,
                        teacher_id, subject_id, color, status, description, start_time,
                        end_time, ref, date, refresh, title, enabled, created_at, timestamp,
                        updated_at, type, teacher_present, force_teacher_present,
                        releaseToken, useToken
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    cal_id, session_id, account_id, local_id, group_session_id, room_id,
                    teacher_id, subject_id, color, status, description, start_time,
                    end_time, ref, date, refresh, title, enabled, created_at, timestamp,
                    updated_at, type_val, teacher_present, force_teacher_present,
                    releaseToken, useToken
                ))

                result["success_count"] += 1
                print(f"✔ Calendar ID {cal_id} inserted successfully")

            except Exception as err:
                error_msg = f"❌ Error inserting Calendar ID {cal.get('id', 'unknown')}: {err}"
                print(error_msg)
                result["error_count"] += 1
                result["errors"].append({"calendar_id": cal.get("id", "unknown"), "error": str(err), "record_number": i})
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


def update_calendar_data(conn, calendar_data):
    """
    Update 'relation_calander_group_session' data in MariaDB.
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
        updated_calendar = calendar_data.get("updated", [])
        result["total_processed"] = len(updated_calendar)

        if not updated_calendar:
            print("No calendar records to update")
            return result

        print(f"Updating {len(updated_calendar)} calendar record(s)...")

        for i, cal in enumerate(updated_calendar, 1):
            try:
                cal_id = cal.get("id")
                if not cal_id:
                    raise ValueError("Missing required field: id")

                # New data mapping
                new_data = {
                    "session_id": cal.get("sessionId"),
                    "account_id": cal.get("accountId"),
                    "local_id": cal.get("localId"),
                    "group_session_id": cal.get("groupId"),
                    "room_id": cal.get("roomId"),
                    "teacher_id": cal.get("teacherId"),
                    "subject_id": cal.get("subjectId"),
                    "color": cal.get("color"),
                    "status": 1 if cal.get("status", True) else 0,
                    "description": cal.get("description"),
                    "start_time": format_date(cal.get("start_time")),
                    "end_time": format_date(cal.get("end_time")),
                    "ref": cal.get("ref"),
                    "date": format_date(cal.get("date")),
                    "refresh": 1 if cal.get("refresh", False) else 0,
                    "title": cal.get("title", ""),
                    "enabled": 1 if cal.get("enabled", True) else 0,
                    "created_at": format_date(cal.get("createdAt")),
                    "timestamp": format_date(cal.get("timestamp")),
                    "updated_at": format_date(cal.get("updatedAt")),
                    "type": cal.get("type"),
                    "teacher_present": 1 if cal.get("teacher_present", False) else 0,
                    "force_teacher_present": 1 if cal.get("force_teacher_present", False) else 0,
                    "releaseToken": 1 if cal.get("releaseToken", False) else 0,
                    "useToken": cal.get("useToken")
                }

                # Fetch existing data
                cursor.execute("SELECT * FROM relation_calander_group_session WHERE id = %s", (cal_id,))
                existing = cursor.fetchone()
                if not existing:
                    print(f"⚠️ Calendar ID {cal_id} not found — skipping update")
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
                    print(f"⏭️ Calendar ID {cal_id} — no changes detected (skipped)")
                    result["skipped_count"] += 1
                    continue

                # Update only if different
                cursor.execute("""
                    UPDATE relation_calander_group_session SET
                        session_id=%s, account_id=%s, local_id=%s, group_session_id=%s,
                        room_id=%s, teacher_id=%s, subject_id=%s, color=%s, status=%s,
                        description=%s, start_time=%s, end_time=%s, ref=%s, date=%s,
                        refresh=%s, title=%s, enabled=%s, created_at=%s, timestamp=%s,
                        updated_at=%s, type=%s, teacher_present=%s, force_teacher_present=%s,
                        releaseToken=%s, useToken=%s
                    WHERE id=%s
                """, (
                    new_data["session_id"], new_data["account_id"], new_data["local_id"], new_data["group_session_id"],
                    new_data["room_id"], new_data["teacher_id"], new_data["subject_id"], new_data["color"],
                    new_data["status"], new_data["description"], new_data["start_time"], new_data["end_time"],
                    new_data["ref"], new_data["date"], new_data["refresh"], new_data["title"], new_data["enabled"],
                    new_data["created_at"], new_data["timestamp"], new_data["updated_at"], new_data["type"],
                    new_data["teacher_present"], new_data["force_teacher_present"],
                    new_data["releaseToken"], new_data["useToken"], cal_id
                ))

                result["success_count"] += 1
                print(f"✔ Calendar ID {cal_id} updated successfully")

            except Exception as err:
                error_msg = f"❌ Error updating Calendar ID {cal.get('id', 'unknown')}: {err}"
                print(error_msg)
                result["error_count"] += 1
                result["errors"].append({"calendar_id": cal.get("id", "unknown"), "error": str(err), "record_number": i})
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
