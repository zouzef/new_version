from datetime import datetime
import json
import os
import sys

# Allow importing common_function.py from same folder
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common_function import format_date


def push_relation_user_sessions(conn, relation_user_session_data):
    """
    Insert 'relation_user_session' data into MariaDB.
    - Inserts only if record does not exist.
    - Skips if the same record already exists.
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
        created_relations = relation_user_session_data.get("created", [])
        updated_relations = relation_user_session_data.get("updated", [])
        all_relations = created_relations + updated_relations
        result["total_processed"] = len(all_relations)

        print(f"Processing {len(all_relations)} relation_user_session record(s)...")

        for i, rel in enumerate(all_relations, 1):
            try:
                relation_id = rel.get("id")
                if not relation_id:
                    raise ValueError("Missing required field: id")

                user_id = rel.get("userId")
                session_id = rel.get("sessionId")
                relation_group = rel.get("relationGroup")
                ref = rel.get("ref")
                enabled = 1 if rel.get("enabled", True) else 0
                release_token = 1 if rel.get("releaseToken", False) else 0
                use_token = rel.get("useToken")

                created_at = format_date(rel.get("createdAt"))
                updated_at = format_date(rel.get("updatedAt"))
                timestamp = format_date(rel.get("timestamp"))

                # Check if this record already exists
                cursor.execute("SELECT * FROM relation_user_session WHERE id = %s", (relation_id,))
                existing = cursor.fetchone()

                if existing:
                    # Check if data is identical
                    same_data = True
                    compare_fields = {
                        "user_id": user_id,
                        "session_id": session_id,
                        "relation_group_local_session_id": relation_group,
                        "ref": ref,
                        "enabled": enabled,
                        "created_at": created_at,
                        "timestamp": timestamp,
                        "updated_at": updated_at,
                        "releaseToken": release_token,
                        "useToken": use_token,
                    }

                    for key, val in compare_fields.items():
                        old_val = str(existing.get(key)) if existing.get(key) is not None else None
                        new_val = str(val) if val is not None else None
                        if old_val != new_val:
                            same_data = False
                            break

                    if same_data:
                        print(f"⏭️  Relation ID {relation_id} already exists — no changes (skipped).")
                        result["skipped_count"] += 1
                        continue

                print(f"Inserting relation_user_session {i}/{len(all_relations)} - ID {relation_id}")

                cursor.execute("""
                    INSERT INTO relation_user_session (
                        id, user_id, session_id, relation_group_local_session_id, ref,
                        enabled, created_at, timestamp, updated_at, releaseToken, useToken
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    relation_id, user_id, session_id, relation_group, ref,
                    enabled, created_at, timestamp, updated_at,
                    release_token, use_token
                ))

                result["success_count"] += 1
                print(f"✔ Relation_user_session ID {relation_id} inserted successfully")

            except Exception as err:
                error_msg = f"❌ Error inserting relation_user_session ID {rel.get('id', 'unknown')}: {err}"
                print(error_msg)
                result["error_count"] += 1
                result["errors"].append({
                    "relation_id": rel.get("id", "unknown"),
                    "error": str(err),
                    "record_number": i
                })
                continue

        conn.commit()
        print(f"\n✅ Inserted: {result['success_count']}")
        print(f"⏭️ Skipped (already exist): {result['skipped_count']}")
        print(f"⚠️ Errors: {result['error_count']}")
        print(f"🧮 Total processed: {result['total_processed']}")

    except Exception as err:
        print(f"💥 Database error: {err}")
        conn.rollback()
    finally:
        if cursor:
            cursor.close()

    return result



def update_relation_user_session(conn, relation_user_session_data):
    """
    Update 'relation_user_session' data in the MariaDB relation_user_session table.
    - Updates only if data is different.
    - Skips if identical.
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
        updated_relations = relation_user_session_data.get("updated", [])
        result["total_processed"] = len(updated_relations)

        if not updated_relations:
            print("No relation_user_session records to update")
            return result

        print(f"🔄 Updating {len(updated_relations)} relation_user_session record(s)...")

        for i, rel in enumerate(updated_relations, 1):
            try:
                relation_id = rel.get("id")
                if not relation_id:
                    raise ValueError("Missing required field: id")

                new_data = {
                    "ref": rel.get("ref"),
                    "session_id": rel.get("sessionId"),
                    "user_id": rel.get("userId"),
                    "relation_group_local_session_id": rel.get("relationGroup"),
                    "enabled": 1 if rel.get("enabled", True) else 0,
                    "timestamp": format_date(rel.get("timestamp")),
                    "created_at": format_date(rel.get("createdAt")),
                    "updated_at": format_date(rel.get("updatedAt")),
                    "releaseToken": 1 if rel.get("releaseToken", False) else 0,
                    "useToken": rel.get("useToken")
                }

                # Check if record exists
                cursor.execute("SELECT * FROM relation_user_session WHERE id = %s", (relation_id,))
                existing = cursor.fetchone()

                if not existing:
                    print(f"⚠️  Relation_user_session ID {relation_id} not found — skipping.")
                    continue

                # Compare data
                same_data = True
                for key, val in new_data.items():
                    old_val = str(existing.get(key)) if existing.get(key) is not None else None
                    new_val = str(val) if val is not None else None
                    if old_val != new_val:
                        same_data = False
                        break

                if same_data:
                    result["skipped_count"] += 1
                    print(f"⏭️  Relation_user_session ID {relation_id} — no changes detected (skipped).")
                    continue

                # Perform update
                cursor.execute("""
                    UPDATE relation_user_session SET
                        ref = %s,
                        session_id = %s,
                        user_id = %s,
                        relation_group_local_session_id = %s,
                        enabled = %s,
                        timestamp = %s,
                        created_at = %s,
                        updated_at = %s,
                        releaseToken = %s,
                        useToken = %s
                    WHERE id = %s
                """, (
                    new_data["ref"], new_data["session_id"], new_data["user_id"],
                    new_data["relation_group_local_session_id"], new_data["enabled"],
                    new_data["timestamp"], new_data["created_at"], new_data["updated_at"],
                    new_data["releaseToken"], new_data["useToken"], relation_id
                ))

                if cursor.rowcount > 0:
                    result["success_count"] += 1
                    print(f"✔ Relation_user_session ID {relation_id} updated successfully")
                else:
                    print(f"⚠️  Relation_user_session ID {relation_id} update executed, but no rows affected")

            except Exception as err:
                msg = f"❌ Error updating relation_user_session ID {rel.get('id', 'unknown')}: {err}"
                print(msg)
                result["error_count"] += 1
                result["errors"].append({
                    "relation_id": rel.get("id", "unknown"),
                    "error": str(err),
                    "record_number": i
                })
                continue

        conn.commit()
        print("\n=== Summary ===")
        print(f"✅ Updated: {result['success_count']}")
        print(f"⏭️ Skipped (no change): {result['skipped_count']}")
        print(f"⚠️ Errors: {result['error_count']}")
        print(f"🧮 Total processed: {result['total_processed']}")

    except Exception as err:
        print(f"💥 Database error: {err}")
        conn.rollback()
    finally:
        if cursor:
            cursor.close()

    return result
