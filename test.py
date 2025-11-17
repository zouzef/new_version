import mysql.connector
import requests
import json
import time
from send_data_api.send_DataViaApi import *

with open("config.json","r") as f:
    config = json.load(f)

db_config = config["databaseConfig"]

def process_audit():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT audit_id, action_type, old_data, new_data, changed_at, is_synced, id_attendance FROM attendance_audit WHERE is_synced = 0       """)
        rows = cursor.fetchall()
        if not rows:
            print("No rows process")
            return
        for row in rows :
            attendance_id = row['id_attendance']
            action_type = row['action_type']
            success = False

            try:
                old_data = json.loads(row['old_data']) if row['old_data'] else {}
                new_data = json.loads(row['old_data']) if row['new_data'] else {}

                #check which type of action this is
                if action_type == "UPDATE":
                    note_changed = old_data.get('note') != new_data.get('note')
                    present_changed = old_data.get('is_present') != new_data.get('is_present')
                    enabled_changed = old_data.get('enabled') != new_data.get('enabled')

                    if note_changed :
                        note = new_data.get('note')
                        print(f" NOte changed for atendance {attendance_id}: {note}")
                        success = send_attendanceNote_to_remote(attendance_id, note)
                    elif present_changed:
                        is_present = new_data.get('is_present')
                        print(f" is_present changed for attendance {attendance_id}: {is_present}")
                        success = send_attendancePresence_to_remote(attendance_id,is_present)
                    elif enabled_changed:
                        enabled = new_data.get('enabled')
                        print(f" enabled changed for attendance{attendance_id}: {enabled}")
                        successs = delete_attendance_to_remote(attendance_id)
                    else:
                        print(f" New student inserted for attendance {attendance_id}")

                        try:
                            new_data = json.loads(row["new_data"]) if isinstance(row["new_data"],str)else row["new_data"]
                            success = send_NewAttendance_to_remote(new_data)
                            print(success)
                        except json.JSONDecodeError:
                            print(f"Invalid JSON in new_data for audit {row['audit_id']}")