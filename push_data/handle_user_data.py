from datetime import datetime
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common_function import format_date



import json

def push_users(conn, user_data):
    """
    Push 'user' data from API into the MariaDB user table.
    - Inserts only new users (if user ID doesn't exist).
    - Skips if the ID already exists.
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
        created_users = user_data.get("created", [])
        updated_users = user_data.get("updated", [])
        all_users = created_users + updated_users
        result["total_processed"] = len(all_users)

        print(f"Processing {len(all_users)} user record(s)...")

        for i, user in enumerate(all_users, 1):
            try:
                user_id = user.get("userId")
                if not user_id:
                    raise ValueError("Missing required field: userId")

                # Check if user already exists
                cursor.execute("SELECT id FROM user WHERE id = %s", (user_id,))
                if cursor.fetchone():
                    print(f"⏭️  User ID {user_id} already exists — skipping insert.")
                    result["skipped_count"] += 1
                    continue  # Skip existing users

                # Map API fields
                uuid = user.get("uuid")
                username = user.get("username", "")
                full_name = user.get("fullName")
                email = user.get("email", "")
                phone = user.get("phone")
                address = user.get("address")
                roles = user.get("roles", [])
                img_link = user.get("image")
                status = 1 if user.get("status") else 0
                enabled = 1 if user.get("enabled", True) else 0
                grand = user.get("grand")
                release_token = 1 if user.get("releaseToken", False) else 0
                use_token = user.get("useToken")
                roles_json = json.dumps(roles) if roles else json.dumps([])

                # Default static fields
                account_id = None
                reset_token = None
                created_by = 0
                password = "TEMP_PASSWORD_NEEDS_RESET"
                birth_date = None
                birth_place = None
                access_type = None
                access_type_date = None
                facebook_id = None
                google_id = None
                mastodon_access_token = None
                general_notification = 1
                message_notification = 1
                calendar_notification = 1
                sms_notification = 1
                login_notification = 1
                horsline = 0
                ref_slc = None
                apple_id = None
                open_source_user_name = None
                rocket_chat_user_id = None
                fcm_web = None
                fcm_android = None
                fcm_ios = None

                # Dates
                created_at = format_date(user.get("createdAt"))
                updated_at = format_date(user.get("updatedAt"))
                timestamp = format_date(user.get("timestamp"))

                print(f"Inserting user {i}/{len(all_users)} - ID {user_id}: {username}")

                cursor.execute("""
                    INSERT INTO user (
                        id, account_id, username, email, full_name, roles, img_link,
                        reset_token, status, created_by, password, birth_date, birth_place,
                        phone, address, grand, access_type, access_type_date, enabled,
                        created_at, timestamp, updated_at, uuid, facebook_id, google_id,
                        mastodon_access_token, general_notification, message_notification,
                        calendar_notification, sms_notification, login_notification,
                        horsline, ref_slc, apple_id, open_source_user_name,
                        rocket_chat_user_id, fcm_web, fcm_android, fcm_ios, releaseToken, useToken
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,%s
                    )
                """, (
                    user_id, account_id, username, email, full_name, roles_json, img_link,
                    reset_token, status, created_by, password, birth_date, birth_place,
                    phone, address, grand, access_type, access_type_date, enabled,
                    created_at, timestamp, updated_at, uuid, facebook_id, google_id,
                    mastodon_access_token, general_notification, message_notification,
                    calendar_notification, sms_notification, login_notification,
                    horsline, ref_slc, apple_id, open_source_user_name,
                    rocket_chat_user_id, fcm_web, fcm_android, fcm_ios, release_token, use_token
                ))

                result["success_count"] += 1
                print(f"✔ User ID {user_id} inserted successfully")

            except Exception as err:
                error_msg = f"❌ Error inserting user ID {user.get('userId', 'unknown')}: {err}"
                print(error_msg)
                result["error_count"] += 1
                result["errors"].append({
                    "user_id": user.get("userId", "unknown"),
                    "error": str(err),
                    "record_number": i
                })
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





def update_user(conn, user_data):
    """
    Update 'user' data in the MariaDB user table.
    - If user ID does not exist: prints a warning.
    - If user exists but data is identical: skips update.
    - If user exists and data is different: updates record.
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
        updated_users = user_data.get("updated", [])
        result["total_processed"] = len(updated_users)

        if not updated_users:
            print("No user records to update")
            return result

        print(f"🔄 Updating {len(updated_users)} user record(s)...")

        for i, user in enumerate(updated_users, 1):
            try:
                user_id = user.get("userId")
                if not user_id:
                    raise ValueError("Missing required field: userId")

                # Extract new data
                new_data = {
                    "uuid": user.get("uuid"),
                    "username": user.get("username"),
                    "full_name": user.get("fullName"),
                    "email": user.get("email"),
                    "phone": user.get("phone"),
                    "address": user.get("address"),
                    "roles": json.dumps(user.get("roles", [])) if user.get("roles") else None
                }

                print(f"Processing user {i}/{len(updated_users)} - ID {user_id}: {new_data['username']}")

                # Step 1: Check if user exists
                cursor.execute("SELECT * FROM user WHERE id = %s", (user_id,))
                existing_user = cursor.fetchone()

                if not existing_user:
                    print(f"⚠️  User ID {user_id} not found — skipping.")
                    continue

                # Step 2: Compare data
                same_data = True
                for key, value in new_data.items():
                    # Convert both to strings for safe comparison
                    old_value = str(existing_user.get(key)) if existing_user.get(key) is not None else None
                    new_value = str(value) if value is not None else None
                    if old_value != new_value:
                        same_data = False
                        break

                if same_data:
                    result["skipped_count"] += 1
                    print(f"⏭️  User ID {user_id} — no changes detected (skipped).")
                    continue

                # Step 3: Update only if different
                cursor.execute("""
                    UPDATE user SET
                        uuid = %s,
                        username = %s,
                        full_name = %s,
                        email = %s,
                        phone = %s,
                        address = %s,
                        roles = %s
                    WHERE id = %s
                """, (
                    new_data["uuid"], new_data["username"], new_data["full_name"],
                    new_data["email"], new_data["phone"], new_data["address"],
                    new_data["roles"], user_id
                ))

                if cursor.rowcount > 0:
                    result["success_count"] += 1
                    print(f"✔ User ID {user_id} updated successfully")
                else:
                    print(f"⚠️  User ID {user_id} update query executed, but no changes detected")

            except Exception as err:
                msg = f"❌ Error updating user ID {user.get('userId', 'unknown')}: {err}"
                print(msg)
                result["error_count"] += 1
                result["errors"].append({"user_id": user.get("userId", "unknown"), "error": str(err)})
                continue

        conn.commit()
        print("\n=== Summary ===")
        print(f"✅ Updated: {result['success_count']}")
        print(f"⏭️  Skipped (no change): {result['skipped_count']}")
        print(f"⚠️  Errors: {result['error_count']}")
        print(f"🧮 Total processed: {result['total_processed']}")

    except Exception as err:
        print(f"💥 Database error: {err}")
        conn.rollback()
    finally:
        if cursor:
            cursor.close()

    return result
