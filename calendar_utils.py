from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'credentials.json'
CALENDAR_ID = 'testeronline11@gmail.com'  # Your calendar ID

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = build('calendar', 'v3', credentials=credentials)

def test_calendar_access():
    try:
        # Try to get calendar info
        calendar = service.calendars().get(calendarId=CALENDAR_ID).execute()
        print(f"Successfully connected to calendar: {calendar.get('summary')}")
        return True
    except Exception as e:
        print(f"Calendar access failed: {str(e)}")
        print("Make sure you've shared your calendar with the service account email:")
        print("Go to Google Calendar → Settings → Share with specific people → Add service account email")
        return False

def check_availability():
    try:
        now = datetime.datetime.utcnow().isoformat() + 'Z'  
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        return events
    except Exception as e:
        print(f"Error checking availability: {str(e)}")
        return []

def create_event(start_time, end_time, summary="Meeting with Raashid's AI Agent"):
    try:
        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time,
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'Asia/Kolkata',
            },
        }

        created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        print(f"Event created: {created_event.get('htmlLink')}")
        return created_event
    except Exception as e:
        print(f"Error creating event: {str(e)}")
        return None

if __name__ == "__main__":
    test_calendar_access()