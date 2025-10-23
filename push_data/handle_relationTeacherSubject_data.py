import sys
import os
from datetime import datetime,timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common_function import format_date


def update_relation_teacher_subject(conn, relation_teacher_subject_data):
    """
    Update 'relation_teacher_to_subject_group' records in MariaDB.
    Only processes 'updated' records.
    """
    result = {
        "success_count": 0,
        "error_count": 0,
        "skipped_count": 0,
        "errors": [],
        "total_processed": 0
    }

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        updated_relations = relation_teacher_subject_data.get("updated", [])
        result["total_processed"] = len(updated_relations)

        if result["total_processed"] == 0:
            print("No relation_teacher_to_subject_group records to update")
            return result

        print(f"🔄 Updating {len(updated_relations)} relation_teacher_to_subject_group record(s)")

        def format_date(date_str):
            """Format date string to MySQL datetime format"""
            if not date_str:
                return None
            try:
                if 'T' in date_str:
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00')).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError) as e:
                print(f"⚠️ Warning: Invalid date format '{date_str}', using NULL: {e}")
                return None

        for i, relation in enumerate(updated_relations, 1):
            try:
                relation_id = relation.get("id")
                if not relation_id:
                    raise ValueError("Missing required field: id")

                # Map fields
                group_id = relation.get("groupId")
                subject_id = relation.get("subjectId")
                teacher_id = relation.get("teacherId")
                enabled = 1 if relation.get("enabled", True) else 0

                # Format dates
                timestamp_val = format_date(relation.get("timestamp"))
                created_at = format_date(relation.get("createdAt"))
                updated_at = format_date(relation.get("updatedAt"))

                print(f"Updating {i}/{len(updated_relations)} - ID {relation_id}")

                cursor.execute("""
                    UPDATE relation_teacher_to_subject_group SET
                        relation_group_local_session_id=%s,
                        subject_id=%s,
                        user_id=%s,
                        enabled=%s,
                        timestamp=%s,
                        created_at=%s,
                        updated_at=%s
                    WHERE id=%s
                """, (
                    group_id, subject_id, teacher_id, enabled,
                    timestamp_val, created_at, updated_at, relation_id
                ))

                if cursor.rowcount > 0:
                    result["success_count"] += 1
                    print(f"✔ ID {relation_id} updated successfully")
                else:
                    result["skipped_count"] += 1
                    print(f"⏭️ ID {relation_id} not found (skipped)")

            except Exception as err:
                error_msg = f"❌ Error ID {relation.get('id', 'unknown')}: {err}"
                print(error_msg)
                result["error_count"] += 1
                result["errors"].append({
                    "relation_id": relation.get("id", "unknown"),
                    "error": str(err),
                    "record_number": i
                })
                continue

        conn.commit()
        print(f"✅ Updated {result['success_count']}/{result['total_processed']} records")
        if result["error_count"] > 0:
            print(f"⚠️ {result['error_count']} errors occurred")

    except Exception as err:
        print(f"💥 Database error: {err}")
        result["errors"].append({"type": "Database Error", "error": str(err)})
        try:
            conn.rollback()
            print("🔄 Transaction rolled back")
        except:
            pass
    finally:
        if cursor:
            cursor.close()

    return result


def push_relation_teacher_subject(conn, relation_teacher_subject_data):
    """
    Insert or update 'relation_teacher_to_subject_group' records in MariaDB.
    Processes both 'created' and 'updated' records.
    """
    result = {
        "success_count": 0,
        "error_count": 0,
        "skipped_count": 0,
        "errors": [],
        "total_processed": 0
    }

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        created_relations = relation_teacher_subject_data.get("created", [])
        updated_relations = relation_teacher_subject_data.get("updated", [])
        all_relations = created_relations + updated_relations
        result["total_processed"] = len(all_relations)

        if result["total_processed"] == 0:
            print("No teacher-subject relation records to process")
            return result

        print(f"🔄 Processing {len(all_relations)} teacher-subject relation record(s)")

        def format_date(date_str):
            """Format date string to MySQL datetime format"""
            if not date_str:
                return None
            try:
                if 'T' in date_str:
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00')).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError) as e:
                print(f"⚠️ Warning: Invalid date format '{date_str}', using NULL: {e}")
                return None

        for i, relation in enumerate(all_relations, 1):
            try:
                relation_id = relation.get("id")
                if not relation_id:
                    raise ValueError("Missing required field: id")

                # Map fields
                group_id = relation.get("groupId")
                subject_id = relation.get("subjectId")
                teacher_id = relation.get("teacherId")
                enabled = 1 if relation.get("enabled", True) else 0
                release_token = 1 if relation.get("releaseToken", False) else 0
                use_token = relation.get("useToken")

                # Format dates
                created_at = format_date(relation.get("createdAt"))
                updated_at = format_date(relation.get("updatedAt"))
                timestamp_val = format_date(relation.get("timestamp"))

                print(f"Processing {i}/{len(all_relations)} - ID {relation_id}")

                cursor.execute("""
                    INSERT INTO relation_teacher_to_subject_group (
                        id, relation_group_local_session_id, subject_id, user_id,
                        enabled, created_at, timestamp, updated_at, releaseToken, useToken
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        relation_group_local_session_id=VALUES(relation_group_local_session_id),
                        subject_id=VALUES(subject_id),
                        user_id=VALUES(user_id),
                        enabled=VALUES(enabled),
                        created_at=VALUES(created_at),
                        timestamp=VALUES(timestamp),
                        updated_at=VALUES(updated_at),
                        releaseToken=VALUES(releaseToken),
                        useToken=VALUES(useToken)
                """, (
                    relation_id, group_id, subject_id, teacher_id,
                    enabled, created_at, timestamp_val, updated_at,
                    release_token, use_token
                ))

                result["success_count"] += 1
                print(f"✔ ID {relation_id} processed successfully")

            except Exception as err:
                error_msg = f"❌ Error ID {relation.get('id', 'unknown')}: {err}"
                print(error_msg)
                result["error_count"] += 1
                result["errors"].append({
                    "relation_id": relation.get("id", "unknown"),
                    "error": str(err),
                    "record_number": i
                })
                continue

        conn.commit()
        print(f"✅ Processed {result['success_count']}/{result['total_processed']} records")
        if result["error_count"] > 0:
            print(f"⚠️ {result['error_count']} errors occurred")

    except Exception as err:
        print(f"💥 Database error: {err}")
        result["errors"].append({"type": "Database Error", "error": str(err)})
        try:
            conn.rollback()
            print("🔄 Transaction rolled back")
        except:
            pass
    finally:
        if cursor:
            cursor.close()

    return result


