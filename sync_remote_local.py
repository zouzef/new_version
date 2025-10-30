import mysql.connector
import requests
import json
import time
from send_data_api.send_DataViaApi import *

# Config
with open("config.json") as f:
    config = json.load(f)


db_config = config["databaseConfig"]

import json
import mysql.connector

def process_audit():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT audit_id, action_type, old_data, new_data, changed_at, is_synced, id_attendance
            FROM attendance_audit
            WHERE is_synced = 0
        """)
        rows = cursor.fetchall()

        if not rows:
            print("No rows to process")
            return

        for row in rows:
            attendance_id = row['id_attendance']
            try:
                old_data = json.loads(row['old_data']) if row['old_data'] else {}
                new_data = json.loads(row['new_data']) if row['new_data'] else {}

                note_changed = old_data.get('note') != new_data.get('note')
                present_changed = old_data.get('is_present') != new_data.get('is_present')

                if note_changed:
                    note = new_data.get('note')
                    print(f"📝 Note changed for attendance {attendance_id}: {note}")
                    success = send_attendanceNote_to_remote(attendance_id, note)

                elif present_changed:
                    is_present = new_data.get('is_present')
                    print(is_present)
                    print(f"✅ is_present changed for attendance {attendance_id}: {is_present}")
                    success = send_attendancePresence_to_remote(attendance_id, is_present)

                else:
                    print(f"⚠️ No relevant field changed for attendance {attendance_id}")
                    success = True  # Skip but still mark synced to avoid loops

                if success:
                    cursor.execute("""
                        UPDATE attendance_audit 
                        SET is_synced = 1
                        WHERE audit_id = %s
                    """, (row['audit_id'],))
                else:
                    print(f"❌ Error sending data for attendance {attendance_id}")

            except Exception as inner_e:
                print(f"💥 Error processing audit {row['audit_id']}: {inner_e}")

        conn.commit()

    except Exception as e:
        print(f"💥 Database error: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

while True:
    process_audit()
    time.sleep(20)