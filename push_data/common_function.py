from datetime import datetime,timedelta



def format_date(date_str):
    """Format date string to MySQL datetime format"""
    if not date_str:
        return None  # Let MySQL handle default values
    try:
        if 'T' in date_str:
            # Handle ISO format with timezone
            return datetime.fromisoformat(date_str.replace('Z', '+00:00')).strftime("%Y-%m-%d %H:%M:%S")
        else:
            # Handle already formatted datetime
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError) as e:
        print(f"Warning: Invalid date format '{date_str}', using NULL: {e}")
        return None


def get_slc_mac(conn,account_id):
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
        SELECT mac FROM slc WHERE account_id=%s
        """,(account_id,))

        result = cursor.fetchone()
        if result is None:
            return None
        else:
            return result

        cursor.close()
        return result
    except Exception as err:
        print(f"DEBUG: error is coming from get_slc_mac {err}")
        return None