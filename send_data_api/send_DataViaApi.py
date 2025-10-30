import json
import requests




with open("api_call_unistudious.json", "r") as f:
    api_calls = json.load(f)

with open("config.json", "r") as f1:
    config=json.load(f1)

BASE_URL= api_calls["base_url"]
TOKEN= config["serverConfig"]["TOKEN"]
API_URL_UPDATE_NOTE= api_calls["url_map"]["update_attendance_note"]
API_URL_UPDATE_STATUS= api_calls["url_map"]["update_attendance_status"]
API_URL_DELETE_ATTENDANCE = api_calls["url_map"]["delete_attendance_record"]
headers = {
    "Authorization": f"Bearer {TOKEN}",

}


def send_attendanceNote_to_remote(attendance_id,note):
    """Send attendance record to remote API"""
    payload = {
        'note':note
    }  # Map fields if needed
    try:
        url=f"{BASE_URL}{API_URL_UPDATE_NOTE}{attendance_id}"
        print(url)
        response=requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
        print(response.status_code)

        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error from update note sending to remote: {e}")
        return False


def send_attendancePresence_to_remote(id_attendance,status):
    """send attendance status to remote server"""
    payload ={
        'status':True if status==1 else False
    }
    try:

        url = f"{BASE_URL}{API_URL_UPDATE_STATUS}{id_attendance}"
        print(url)
        response = requests.post(url,data=payload,headers=headers)
        response.raise_for_status()
        print(response.status_code)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error from update status sending to remote: {e}")
        return False


def delete_attendance_to_remote(attendance_id):
    """send attendance record to remote API"""
    payload = {
        'attendanceId':attendance_id
    }  # Map fields if needed
    try:
        url=f"{BASE_URL}{API_URL_DELETE_ATTENDANCE}{attendance_id}"
        print(url)
        response=requests.delete(url, data=payload, headers=headers)
        response.raise_for_status()
        print(response.status_code)

        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error from delete attendance sending to remote: {e}")
        return False

