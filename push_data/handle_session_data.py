import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common_function import format_date


def insert_session_data(conn, session_data):
    """
    Insert session data into the 'session' table.
    - Inserts only new sessions (if ID doesn't exist)
    - Skips if session ID already exists
    - Fills defaults for required fields to avoid DB errors
    """
    result = {"success_count":0, "error_count":0, "skipped_count":0, "errors":[], "total_processed":0}
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        created_sessions = session_data.get("created", []) or []
        updated_sessions = session_data.get("updated", []) or []
        all_sessions = created_sessions + updated_sessions
        result["total_processed"] = len(all_sessions)

        if not all_sessions:
            print("No session records to process")
            return result

        print(f"Processing {len(all_sessions)} session record(s)")

        for i, session in enumerate(all_sessions, 1):
            try:
                session_id = session.get("id")
                if not session_id:
                    raise ValueError("Missing required field: id")

                # Skip if session already exists
                cursor.execute("SELECT id FROM session WHERE id=%s", (session_id,))
                if cursor.fetchone():
                    print(f"⏭️ Session ID {session_id} already exists — skipping insert.")
                    result["skipped_count"] += 1
                    continue

                # Map fields with safe defaults
                data = {
                    "uuid": session.get("uuid"),
                    "account_id": session.get("accountId"),
                    "formation_id": session.get("formationId"),
                    "name": session.get("name", ""),
                    "description": session.get("description"),
                    "status": 1 if session.get("status", True) else 0,
                    "img_link": session.get("image"),
                    "start_date": format_date(session.get("startDate")),
                    "end_date": format_date(session.get("endDate")),
                    "capacity": session.get("capacity", 0),
                    "price": session.get("price", 0),
                    "currency": session.get("currency"),
                    "type_pay": session.get("typePay"),
                    "request_change_group": 1 if session.get("requestChangeGroup", False) else 0,
                    "max_group_change": session.get("maxGroupChange", 0),
                    "special_group": 1 if session.get("specialGroup", False) else 0,
                    "enabled": 1 if session.get("enabled", True) else 0,
                    "user_register_after_start": 1,
                    "releaseToken": 1 if session.get("releaseToken", False) else 0,
                    "useToken": session.get("useToken"),
                    "created_at": format_date(session.get("createdAt")),
                    "updated_at": format_date(session.get("updatedAt")),
                    "timestamp": format_date(session.get("timestamp")),
                    "payment_methode": None,
                    "number_session_for_pay": None,
                    "price_student_absent": None,
                    "public_resource": None,
                    "price_presence": None,
                    "price_online": None,
                    "passage": None,
                    "season_id": None
                }

                cursor.execute("""
                    INSERT INTO session (
                        id, account_id, formation_id, name, description, status, img_link,
                        start_date, end_date, capacity, price, currency, type_pay,
                        request_change_group, max_group_change, payment_methode,
                        number_session_for_pay, price_student_absent, user_register_after_start,
                        public_resource, enabled, created_at, timestamp, updated_at, uuid,
                        price_presence, price_online, special_group, passage, season_id,
                        releaseToken, useToken
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    session_id, data["account_id"], data["formation_id"], data["name"], data["description"],
                    data["status"], data["img_link"], data["start_date"], data["end_date"], data["capacity"],
                    data["price"], data["currency"], data["type_pay"], data["request_change_group"], data["max_group_change"],
                    data["payment_methode"], data["number_session_for_pay"], data["price_student_absent"],
                    data["user_register_after_start"], data["public_resource"], data["enabled"], data["created_at"],
                    data["timestamp"], data["updated_at"], data["uuid"], data["price_presence"], data["price_online"],
                    data["special_group"], data["passage"], data["season_id"], data["releaseToken"], data["useToken"]
                ))

                result["success_count"] += 1
                print(f"✔ Session ID {session_id} inserted successfully")

            except Exception as e:
                print(f"❌ Error inserting session ID {session.get('id', 'unknown')}: {e}")
                result["error_count"] += 1
                result["errors"].append({"session_id": session.get("id", "unknown"), "error": str(e), "record_number": i})
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


def update_session_data(conn, session_data):
    """
    Update session data in the 'session' table.
    - Skips update if data is identical to existing row
    """
    result = {"success_count":0, "error_count":0, "skipped_count":0, "errors":[], "total_processed":0}
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        updated_sessions = session_data.get("updated", []) or []
        result["total_processed"] = len(updated_sessions)

        if not updated_sessions:
            print("No session records to update")
            return result

        print(f"🔄 Updating {len(updated_sessions)} session record(s)...")

        for i, session in enumerate(updated_sessions, 1):
            try:
                session_id = session.get("id")
                if not session_id:
                    raise ValueError("Missing required field: id")

                # Map new data
                new_data = {
                    "uuid": session.get("uuid"),
                    "account_id": session.get("accountId"),
                    "formation_id": session.get("formationId"),
                    "name": session.get("name"),
                    "description": session.get("description"),
                    "status": 1 if session.get("status", True) else 0,
                    "img_link": session.get("image"),
                    "start_date": format_date(session.get("startDate")),
                    "end_date": format_date(session.get("endDate")),
                    "capacity": session.get("capacity", 0),
                    "price": session.get("price", 0),
                    "currency": session.get("currency"),
                    "type_pay": session.get("typePay"),
                    "request_change_group": 1 if session.get("requestChangeGroup", False) else 0,
                    "max_group_change": session.get("maxGroupChange", 0),
                    "special_group": 1 if session.get("specialGroup", False) else 0,
                    "enabled": 1 if session.get("enabled", True) else 0,
                    "user_register_after_start": 1,
                    "releaseToken": 1 if session.get("releaseToken", False) else 0,
                    "useToken": session.get("useToken"),
                    "created_at": format_date(session.get("createdAt")),
                    "updated_at": format_date(session.get("updatedAt")),
                    "timestamp": format_date(session.get("timestamp")),
                    "payment_methode": None,
                    "number_session_for_pay": None,
                    "price_student_absent": None,
                    "public_resource": None,
                    "price_presence": None,
                    "price_online": None,
                    "passage": None,
                    "season_id": None
                }

                # Step 1: Check existing session
                cursor.execute("SELECT * FROM session WHERE id=%s", (session_id,))
                existing = cursor.fetchone()
                if not existing:
                    print(f"⚠️ Session ID {session_id} not found — skipping update.")
                    result["skipped_count"] += 1
                    continue

                # Step 2: Compare new data to existing
                same_data = True
                for key, value in new_data.items():
                    old_val = str(existing.get(key)) if existing.get(key) is not None else None
                    new_val = str(value) if value is not None else None
                    if old_val != new_val:
                        same_data = False
                        break

                if same_data:
                    result["skipped_count"] += 1
                    print(f"⏭️ Session ID {session_id} — no changes detected (skipped).")
                    continue

                # Step 3: Update only if different
                cursor.execute("""
                    UPDATE session SET
                        uuid=%s, account_id=%s, formation_id=%s, name=%s, description=%s,
                        status=%s, img_link=%s, start_date=%s, end_date=%s, capacity=%s,
                        price=%s, currency=%s, type_pay=%s, request_change_group=%s, max_group_change=%s,
                        special_group=%s, enabled=%s, user_register_after_start=%s,
                        releaseToken=%s, useToken=%s, created_at=%s, updated_at=%s, timestamp=%s,
                        payment_methode=%s, number_session_for_pay=%s, price_student_absent=%s,
                        public_resource=%s, price_presence=%s, price_online=%s, passage=%s, season_id=%s
                    WHERE id=%s
                """, (
                    new_data["uuid"], new_data["account_id"], new_data["formation_id"], new_data["name"],
                    new_data["description"], new_data["status"], new_data["img_link"], new_data["start_date"],
                    new_data["end_date"], new_data["capacity"], new_data["price"], new_data["currency"], new_data["type_pay"],
                    new_data["request_change_group"], new_data["max_group_change"], new_data["special_group"],
                    new_data["enabled"], new_data["user_register_after_start"], new_data["releaseToken"], new_data["useToken"],
                    new_data["created_at"], new_data["updated_at"], new_data["timestamp"], new_data["payment_methode"],
                    new_data["number_session_for_pay"], new_data["price_student_absent"], new_data["public_resource"],
                    new_data["price_presence"], new_data["price_online"], new_data["passage"], new_data["season_id"], session_id
                ))
                result["success_count"] += 1
                print(f"✔ Session ID {session_id} updated successfully")

            except Exception as e:
                print(f"❌ Error updating session ID {session.get('id', 'unknown')}: {e}")
                result["error_count"] += 1
                result["errors"].append({"session_id": session.get("id", "unknown"), "error": str(e), "record_number": i})
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