import mysql.connector
import requests
import time
import json
import os
from datetime import datetime, timedelta
import push_data


#file of the configuration
with open("config.json","r") as f:
    config=json.load(f)


# Extract server and database configurations
server_config = config["serverConfig"]
database_config = config["databaseConfig"]

# Set configuration variables
TOKEN = server_config["TOKEN"]
SYNC_INTERVAL_MINUTES = server_config["SYNC_INTERVAL_MINUTES"]
SYNC_STATUS_FILE = server_config["SYNC_STATUS_FILE"]
INTERNET_CHECK_TIMEOUT = server_config["INTERNET_CHECK_TIMEOUT"]
INTERNET_CHECK_URL = server_config["INTERNET_CHECK_URL"]



def check_internet_connection():
    try:
        print("checking internet connection...")
        response = requests.get(INTERNET_CHECK_URL,timeout=INTERNET_CHECK_TIMEOUT)
        return response.status_code == 200
    except (requests.ConnectionError,requests.Timeout):
        print("No internet connection availble")
        return False


#function to conncect to database
def create_db_connection(db_config):
    try:
        print(f"Attempting to connect to MariaDB at {db_config['host']}:{db_config['port']}")
        conn = mysql.connector.connect(**db_config)
        print("MairaDB connection established successfully")
        return conn
    except mysql.connector.Error as e:
        print(f"Failed to connect to MariaDB: {e}")
        raise



#function for the time of the syncrosation

def get_last_sync_time():
    try:
        if os.path.exists(SYNC_STATUS_FILE):
            with open(SYNC_STATUS_FILE,'r')as f:
                data = json.load(f)
                last_sync_str = data.get('last_sync_time')
                if last_sync_str:
                    last_sync_time = datetime.fromisoformat(last_sync_str)
                    print(f"Last sync time from file: {last_sync_time}")
                    return last_sync_time
                else:
                    print("No valid sync time found in file ")
                    return None
        else:
            print("Sync status file does not exist")
            return None

    except (json.JSONDecodeError,ValueError,FileNotFoundError) as err:
        print(f"Error reading sync status file: {err}")
        print("Will perform full sync")
        return None



#function to save the function tha save the date of last synchronisation
def save_last_sync_time(sync_time):

    try:
        sync_data = {
            'last_sync_time':sync_time.isoformat(),
            'updated_at':datetime.now().isoformat()
        }

        if os.path.exists(SYNC_STATUS_FILE):
            backup_file = f"{SYNC_STATUS_FILE}.backup"
            with open(SYNC_STATUS_FILE, 'r') as original:
                with open(backup_file, 'w') as backup:
                    backup.write(original.read())

        #Write new sync time
        with open(SYNC_STATUS_FILE,'w') as f:
            json.dump(sync_data,f,indent=2)

        print(f"Sync time saved to file: {sync_time}")


    except Exception as err:
        print(f"Error saving sync time to file: {err}")


#funtion to fetch data from the remote server
def fetch_data(tkoen, since_date=None):
    try:
        url = "https://unistudious.com/slc/get-whats-news"
        headers= {"Authorization": f"Bearer {tkoen}"}
        payload={}
        if since_date:
            # Subtract 1 hour from the provided date
            adjusted_date = since_date - timedelta(hours=1)
            # Format date without seconds (YYYY-MM-DD HH:MM)
            payload['date'] = adjusted_date.strftime("%Y-%m-%d %H:%M")
            print(f"Fetching data since (adjusted -1 hour): {payload['date']}")

        else:
            print("Fetching full data(intial sync)")

        response = requests.post(url,headers=headers,data=payload)
        response.raise_for_status()
        return response.json()

    except requests.RequestException as err:
        print(f"API request failed: {err}")
        raise


def process_created_updated(conn, label, data, push_fn):

    try:
        #Case 1: API returns a dict with created/updated
        if isinstance(data,dict):
            if "created" in data and data["created"]:
                print(f"\n ---Processing New {label} ---")
                push_fn(conn,data["created"])
            if "updated" in data and data["updated"]:
                print(f"\n ---Processing Updated {label} ---")
                push_fn(conn,data["updated"])
            if "updated" in data and data["updated"]:
                print(f"\n ---Processing Deleted {label} ---")
                push_fn(conn,data["updated"])

        # Case 2: API returns a plain list
        elif isinstance(data,list) and data:
            print(f"\n--- Processing{label} list ({len(data)} records) ---")
            push_fn(conn, data)

    except Exception as err:
        print(f"Unexpected error while processing {label: {err}}")



def has_new_data(data):
    data_keys = ["user", "account", "local_with_room", "subject", "accountSubject",
                 "attendance", "session", "relationUserSession", "calendar", "group",
                 "relationTeacherAndSubjectData","admin","slcTablet"]
    for key in data_keys:
        section = data.get(key,{})
        if isinstance(section,dict):
            if section.get("created") or section.get("updated"):
                return True
            elif isinstance(section, list) and section:
                return True
    return False


def sync_data_once():
    #first check for internet connection
    if not check_internet_connection():
        print("No internet connection availble.Cannot sync with remote server. ")
        print("Please check you internet connection and try again.")
        return False

    conn = None
    try:
        print(f"\n == Starting sync at {datetime.now()} ===")
        conn = create_db_connection(database_config)

        # Get last sync time from JSON file
        last_sync = get_last_sync_time()

        # Prepare request - store current time before API call
        now_for_next_sync = datetime.now()

        # Use the fetch_data funtion which handles time adjustmenet
        data = fetch_data(TOKEN, last_sync)

        #check if there's any new data
        if not data or not has_new_data(data):
            print("No new data available. Skipping sync.")
            return True

        print("New data founc, procesing...")

        # User - Handle both created and updated
        user_data = data.get("user",{})
        if user_data:
            from push_data.handle_user_data import push_users ,update_user
            print("\n --- Processing User Data ---")

            # Process created records using the existing push function
            if user_data.get("created"):
                print("Processing new user records...")
                push_users(conn,{"created":user_data["created"]})

            # Process updated records using the new update function
            if user_data.get("updated"):
                print("Processing updated user records...")
                update_user(conn,{"updated":user_data["updated"]})

        # Tablet - Handle both created and updated

        tablet_data = data.get("slcTablet", {})
        if tablet_data:
            print("\n--- Processing Tablet Data ---")

            # Process created records using the existing push function
            if tablet_data.get("created"):
                from push_data.handle_tablet_data import push_tablet_data
                print("Processing new tablet records...")
                push_tablet_data(conn,{"created": tablet_data["created"]})

            # Process updated records using the new update function
            if tablet_data.get("updated"):
                from push_data.handle_tablet_data import update_tablet
                print("Processing updated tablet records...")
                update_tablet(conn,{"updated": tablet_data["updated"]})

        # Subject - Handle both created and updated
        subject_data = data.get("subject", {})
        if subject_data:
            print("\n--- Processing Subject Data ---")

            #process created records using the existing push function
            if subject_data.get("created"):
                from push_data.handle_SubjectConfig_data import push_subjects
                print("Processing new subject records...")
                push_subjects(conn,{"created": subject_data["created"]})

            #process updated rcords using the new update function
            if subject_data.get("updated"):
                from push_data.handle_SubjectConfig_data import update_subjects
                print("Processing updated subject records...")
                update_subjects(conn,{"updated": subject_data["updated"]})

        # Slc_local - Handl both created and updated
        local_slc_data = data.get("slcLocal",{})
        if local_slc_data:
            print("\n--- Processing local SLC Data ---")

            # Process created records using the existing push function
            if local_slc_data.get("created"):
                from push_data.handle_LocalSlc_data import insert_slc_local
                print("Processing new local_slc records...")
                insert_slc_local(conn,{"created": local_slc_data["created"]})


            # Process updated records using the new update function
            if local_slc_data.get("updated"):
                from push_data.handle_LocalSlc_data import update_slc_local
                print("Processing updated local SLC records")
                update_slc_local(conn,{"updated": local_slc_data["updated"]})


        # Slc - Handle both created and updated
        slc_data = data.get("slc", {})
        if( slc_data):
            print("\n--- Processing Slc Data ---\n")
            if (slc_data.get("created")):
                print("\n--- Processing new slc Data ---")
                from push_data.handle_slc_data import insert_slc_data
                insert_slc_data(conn,{"created": slc_data["created"]})

            if (slc_data.get("updated")):
                print("\n--- Processing updated slc data ---")
                from push_data.handle_slc_data import updated_slc_data
                updated_slc_data(conn,{"updated": slc_data["updated"]})


        # Session - Handle both created and updated
        session_data= data.get("session", {})
        if (session_data):
            print("\n ---Processing Session Data ---")

            # Process created recordsusing he existing push function
            if session_data.get("created"):
                print("Processing new session records...")
                from push_data.handle_session_data import insert_session_data
                insert_session_data(conn,{"created": session_data["created"]})

            # Process updated records using the new update function
            if session_data.get("updated"):
                print("Processing updated session records...")
                from push_data.handle_session_data import update_session_data
                update_session_data(conn,{"updated": session_data["updated"]})


        # Local|Room - Handle both created and updated
        local_with_room_data=data.get("local_with_room", {})
        if local_with_room_data:
            print("\n--- Processing Local with Room Data ---")

            # Process created records using the existing push functon
            if local_with_room_data.get("created"):
                print("\n--- Processing new local with room records ---")
                from push_data.handle_room_data import insert_room_data
                insert_room_data(conn,{"created": local_with_room_data["created"]})

            # Process updated records using the new update function
            if local_with_room_data.get("updated"):
                print("\n--- Processing updated local with room records ---")
                from push_data.handle_room_data import update_room_data
                update_room_data(conn,{"updated": local_with_room_data["updated"]})

        # Relation User Session - Handle both created and updated
        relationsession = data.get("relationUserSession", {})
        if relationsession:
            print("\n--- Processing Relation User Session Data ---")

            # Process created records using the existing push function
            if relationsession.get("created"):
                print("\n---processing new relation user session records---")
                from push_data.handle_relationUserSession_data import push_relation_user_sessions
                push_relation_user_sessions(conn,{"created": relationsession["created"]})


            if relationsession.get("updated"):
                print("\n--- Procesing update user sesion records ---")
                from push_data.handle_relationUserSession_data import update_relation_user_session
                update_relation_user_session(conn,{"updated": relationsession["updated"]})


        # Group - handle both created and updated with duplicate filtring
        teacher_subject_data = data.get("relationTeacherAndSubjectData", {})
        if teacher_subject_data:
            print("\n--- Processing Teacher-subject Relation Data ---")

            # Process created records using the existing push function
            if teacher_subject_data.get("created"):
                print("Processing new teacher-subject relation records...")
                from push_data.handle_relationTeacherSubject_data import update_relation_teacher_subject
                update_relation_teacher_subject(conn,{"created":teacher_subject_data["created"]})

            if teacher_subject_data.get("updated"):
                print("Processing updating teacher-subject relation records...")
                from push_data.handle_relationTeacherSubject_data import push_relation_teacher_subject
                push_relation_teacher_subject(conn,{"updated":teacher_subject_data["updated"]})




        # Save the new sync time
        save_last_sync_time(now_for_next_sync)

    except Exception as e:
        print(f"DEBUG:Error {e}")




def run_continuous_sync():
    """Run sync continuously every X minutes"""
    print(f"Starting automatic sync every {SYNC_INTERVAL_MINUTES} minute(s)")
    print("Press Ctrl+C to stop")

    try:
        while True:
            if check_internet_connection():
                sync_data_once()
                print(f"Waiting {SYNC_INTERVAL_MINUTES} minute(s) for next sync...")
            else:
                print("No internet connection. Waiting 1 minute before checking again...")
            time.sleep(SYNC_INTERVAL_MINUTES * 60)
    except KeyboardInterrupt:
        print("\nSync stopped by user")
    except Exception as err:
        print(f"Continuous sync error: {err}")


def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        run_continuous_sync()
    else:
        print("Running single sync...")
        print("Use 'python main.py --continuous' for automatic sync")
        if check_internet_connection():
            sync_data_once()
        else:
            print("Cannot sync: No internet connection available")


if __name__ == "__main__":
    main()