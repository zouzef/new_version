# ===> Download reference student images and organize them <===

import os
import sys
import json
import base64
import requests
import mysql.connector

# Config files
with open("config.json", "r") as f:
    config = json.load(f)
with open("api_call_unistudious.json") as f:
    api_calls = json.load(f)

TOKEN = config["serverConfig"]["TOKEN"]
BASE_URL = api_calls["base_url"]
db_config = config["databaseConfig"]

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

end_point_getRef = api_calls["url_map"]["get-reference-student"]
end_point_read = api_calls["url_map"]["read-file"]

# Main folder for all students
MAIN_FOLDER = "user_students"
os.makedirs(MAIN_FOLDER, exist_ok=True)

def download_image(id_user, file_path):
    """Download a single image from the API and save it under the user's folder if not already exists."""
    user_folder = os.path.join(MAIN_FOLDER, str(id_user))
    os.makedirs(user_folder, exist_ok=True)

    file_name = os.path.basename(file_path)
    local_path = os.path.join(user_folder, file_name)

    # ✅ Skip download if image already exists
    if os.path.exists(local_path):
        print(f"⚡ Image already exists locally, skipping: {local_path}")
        return

    url = f"{BASE_URL}{end_point_read}"
    payload = {"fileName": file_path}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()
        if "content" in data:
            image_data = base64.b64decode(data["content"])

            with open(local_path, "wb") as f:
                f.write(image_data)
            print(f"[+] Image saved at {local_path}")
        else:
            print(f"[-] No 'content' field in response for user {id_user}")
    except Exception as e:
        print(f"[-] Error downloading image for user {id_user}: {e}")

def get_student_references(id_user):
    """Get all reference images for a student and download only those that don’t exist."""
    try:
        url = f"{BASE_URL}{end_point_getRef}{id_user}"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        file_list = data.get("fileList", [])

        if file_list:
            for file_path in file_list:
                download_image(id_user, file_path)
        else:
            print(f"[-] No reference images found for user {id_user}")
    except Exception as e:
        print(f"[-] Error fetching references for user {id_user}: {e}")

def get_all_student_ids():
    """Fetch all student IDs that have a reference image."""
    student_ids = []
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM user WHERE ref_slc IS NOT NULL")
        results = cursor.fetchall()
        student_ids = [r[0] for r in results]
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[-] Error fetching student IDs: {e}")
    return student_ids

if __name__ == "__main__":
    all_student_ids = get_all_student_ids()
    print(f"[+] Found {len(all_student_ids)} students with references.")

    for student_id in all_student_ids:
        get_student_references(student_id)
