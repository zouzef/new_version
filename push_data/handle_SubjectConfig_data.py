import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common_function import format_date



def push_subjects(conn, subject_data):
    """
    Insert 'subject' records into subject_config table.
    - Skips insert if subject ID already exists.
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
        created_subjects = subject_data.get("created", [])
        result["total_processed"] = len(created_subjects)

        if not created_subjects:
            print("No new subjects to insert")
            return result

        print(f"Processing {len(created_subjects)} new subject(s)...")

        for i, subj in enumerate(created_subjects, 1):
            try:
                subj_id = subj.get("id")
                if not subj_id:
                    raise ValueError("Missing required field: id")

                # Check if subject already exists
                cursor.execute("SELECT id FROM subject_config WHERE id = %s", (subj_id,))
                if cursor.fetchone():
                    print(f"⏭️  Subject ID {subj_id} already exists — skipping insert.")
                    result["skipped_count"] += 1
                    continue

                # Map fields
                name = subj.get("name", "")
                status = 1 if subj.get("status", True) else 0
                description = subj.get("description", "")
                enabled = 1 if subj.get("enabled", True) else 0
                releaseToken = 1 if subj.get("releaseToken", False) else 0
                useToken = subj.get("useToken")
                created_at = format_date(subj.get("createdAt"))
                updated_at = format_date(subj.get("updatedAt"))
                timestamp = format_date(subj.get("timestamp"))

                cursor.execute("""
                    INSERT INTO subject_config (
                        id, name, status, description, enabled,
                        created_at, updated_at, timestamp, releaseToken, useToken
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (subj_id, name, status, description, enabled,
                      created_at, updated_at, timestamp, releaseToken, useToken))

                result["success_count"] += 1
                print(f"✔ Subject ID {subj_id} inserted successfully")

            except Exception as err:
                print(f"❌ Error inserting subject ID {subj.get('id', 'unknown')}: {err}")
                result["error_count"] += 1
                result["errors"].append({"subject_id": subj.get("id", "unknown"), "error": str(err)})
                continue

        conn.commit()

    except Exception as err:
        print(f"💥 Database error: {err}")
        conn.rollback()
    finally:
        if cursor:
            cursor.close()

    return result


def update_subject(conn, subject_data):
    """
    Update 'subject' records in subject_config table.
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
        updated_subjects = subject_data.get("updated", [])
        result["total_processed"] = len(updated_subjects)

        if not updated_subjects:
            print("No subjects to update")
            return result

        print(f"Processing {len(updated_subjects)} updated subject(s)...")

        for i, subj in enumerate(updated_subjects, 1):
            try:
                subj_id = subj.get("id")
                if not subj_id:
                    raise ValueError("Missing required field: id")

                # Extract new data
                new_data = {
                    "name": subj.get("name"),
                    "status": 1 if subj.get("status", True) else 0,
                    "description": subj.get("description"),
                    "enabled": 1 if subj.get("enabled", True) else 0,
                    "releaseToken": 1 if subj.get("releaseToken", False) else 0,
                    "useToken": subj.get("useToken"),
                    "timestamp": format_date(subj.get("timestamp")),
                    "updated_at": format_date(subj.get("updatedAt"))
                }

                # Fetch existing subject
                cursor.execute("SELECT * FROM subject_config WHERE id = %s", (subj_id,))
                existing = cursor.fetchone()
                if not existing:
                    print(f"⚠️  Subject ID {subj_id} not found — skipping update.")
                    result["skipped_count"] += 1
                    continue

                # Compare data
                identical = True
                for key, val in new_data.items():
                    old_val = existing.get(key)
                    if old_val != val:
                        identical = False
                        break

                if identical:
                    print(f"⏭️  Subject ID {subj_id} — no changes detected, skipping.")
                    result["skipped_count"] += 1
                    continue

                # Update only if different
                cursor.execute("""
                    UPDATE subject_config SET
                        name=%s, status=%s, description=%s, enabled=%s,
                        releaseToken=%s, useToken=%s, timestamp=%s, updated_at=%s
                    WHERE id=%s
                """, (new_data["name"], new_data["status"], new_data["description"],
                      new_data["enabled"], new_data["releaseToken"], new_data["useToken"],
                      new_data["timestamp"], new_data["updated_at"], subj_id))

                if cursor.rowcount > 0:
                    result["success_count"] += 1
                    print(f"✔ Subject ID {subj_id} updated successfully")
                else:
                    print(f"⚠️  Subject ID {subj_id} update executed but no changes applied")

            except Exception as err:
                print(f"❌ Error updating subject ID {subj.get('id', 'unknown')}: {err}")
                result["error_count"] += 1
                result["errors"].append({"subject_id": subj.get("id", "unknown"), "error": str(err)})
                continue

        conn.commit()

    except Exception as err:
        print(f"💥 Database error: {err}")
        conn.rollback()
    finally:
        if cursor:
            cursor.close()

    return result