import mysql.connector
import requests
import json
import os
import time
from datetime import datetime,timedelta

from main_system import server_config, TOKEN
from push_data.handle_attendance_data import insert_attendance,update_attendance_data
# === CONFIG ===

with open("config.json","r") as f:
    config = json.load(f)

db_config = config["databaseCOnfig"]


API_URL = "https://unistudious.com/slc/update-attendance-note"

def send_to_remote(attendance_id,note):
    payload = {
        'note':note,

    }
    headers = {"Authorization": f"Bearer {TOKEN}"}
    try:
        url=f"{API_URL}{attendance_id}"

        response = requests.post(url,data=payload,headers=headers)
        response.raise_for_status()
        print(response.status_code)

        return response.status_code ==200
    except Exception as e:
        print(f"Error sending to remote: {e}")
        return False

def process_audit():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        #select only rows that have releaseToken = 1 AND useToken not NULL
        cursor.execute("""
            SELECT audit_id , action_type, old_data, new_data, changed_at, is_synced, id_attendance
             FROM attendance_audit
            WHERE is_synced = 0
        """)
        rows = cursor.fetchall()
        if (len(rows)==0):
            print("No rows to process")
            return

        for row in rows:
            attendanceId = json.loads(str(row["id_attendance"]))
            note = json.loads(str(row['new_data']))['note']
            if(send_to_remote(attendanceId,note)):
                cursor.execute("""
                UPDATE attendance_audit
                set is_synced = 1
                WHERE id_attendance = %s
                """,(attendanceId, ))
            else:
                print("Error in sending ")
        conn.commit()

    except Exception as e:
        print(f" Database error: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

while True:
    process_audit()
    time.sleep(20)