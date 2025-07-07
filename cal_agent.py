from langchain_google_genai import ChatGoogleGenerativeAI
import os
from langchain.agents import initialize_agent, Tool
from langchain.agents.agent_types import AgentType
from calendar_utils import check_availability, create_event, test_calendar_access
import datetime
import dateparser
import json
import re

# Test calendar access on startup
print("Testing calendar access...")
if not test_calendar_access():
    print("Calendar access failed. Please share your calendar with the service account.")

# Initialize LLM for data extraction
import os
from dotenv import load_dotenv
load_dotenv()
api_key = ("AIzaSyDAUaDWMz4znuWoIGj-rNvRvHiBpEK9h5s")

extraction_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=api_key)

def extract_meeting_details(user_input):
    
    try:
        extraction_prompt = user_input
        
        response = extraction_llm.invoke(extraction_prompt)
        
        # Parse the JSON response
        json_str = response.content.strip()
        # Remove any markdown formatting
        json_str = re.sub(r'```json\n?', '', json_str)
        json_str = re.sub(r'```\n?', '', json_str)
        
        extracted_data = json.loads(json_str)
        return extracted_data
        
    except Exception as e:
        print(f"LLM extraction failed: {e}")
        # Fallback to basic extraction
        return {
            "title": "Meeting",
            "datetime_text": user_input,
            "duration_minutes": 60,
            "notes": ""
        }

# Tool 1: Check calendar availability
def check_avail_tool(input_str):
    try:
        events = check_availability()
        if not events:
            return "Your calendar is completely free with no upcoming events scheduled."
        
        formatted_events = []
        for event in events:
            start_time = event['start'].get('dateTime', event['start'].get('date'))
            # Parse and format the datetime
            if 'T' in start_time:
                dt = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%B %d, %Y at %I:%M %p")
            else:
                formatted_time = start_time
            
            formatted_events.append(f"• {event.get('summary', 'No title')} - {formatted_time}")
        
        return f"Here are your upcoming events:\n" + "\n".join(formatted_events)
    except Exception as e:
        return f"I encountered an error checking your calendar: {str(e)}"

# Tool 2: Create calendar event with LLM-powered extraction
def create_event_tool(input_str):
    try:
        # Use LLM to extract structured data
        meeting_details = extract_meeting_details(input_str)
        
        # Extract details
        title = meeting_details.get('title', 'Meeting')
        datetime_text = meeting_details.get('datetime_text', input_str)
        duration_minutes = meeting_details.get('duration_minutes', 60)
        notes = meeting_details.get('notes', '')
        
        print(f"Extracted details: {meeting_details}")  # Debug info
        
        # Parse the datetime using dateparser
        parsed_datetime = dateparser.parse(datetime_text, settings={
            'PREFER_DATES_FROM': 'future',
            'RELATIVE_BASE': datetime.datetime.now()
        })
        
        if parsed_datetime:
            start_time = parsed_datetime
            # If only date is specified (no time), default to 10 AM
            if start_time.hour == 0 and start_time.minute == 0:
                start_time = start_time.replace(hour=10, minute=0)
        else:
            # Fallback parsing
            time_match = re.search(r'(\d{1,2}):?(\d{0,2})\s*(am|pm|AM|PM)', datetime_text)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                am_pm = time_match.group(3).upper()
                
                if am_pm == 'PM' and hour != 12:
                    hour += 12
                elif am_pm == 'AM' and hour == 12:
                    hour = 0
                
                # Use tomorrow if no specific date
                base_date = datetime.datetime.now() + datetime.timedelta(days=1)
                start_time = base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            else:
                # Ultimate fallback
                start_time = datetime.datetime.now() + datetime.timedelta(hours=1)
        
        end_time = start_time + datetime.timedelta(minutes=duration_minutes)
        
        # Format for Google Calendar API
        start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S+05:30")
        end_str = end_time.strftime("%Y-%m-%dT%H:%M:%S+05:30")
        
        # Add notes to the event description if provided
        event_description = notes if notes else "Created by AI Calendar Agent"
        
        # Create the event with proper title
        created_event = create_event(start_str, end_str, title)
        
        if created_event:
            formatted_time = start_time.strftime("%B %d, %Y at %I:%M %p")
            duration_text = f" ({duration_minutes} minutes)" if duration_minutes != 60 else ""
            return f"Successfully scheduled '{title}' for {formatted_time}{duration_text}! Event ID: {created_event.get('id')}"
        else:
            return "Failed to create calendar event. Please check permissions."
            
    except Exception as e:
        return f"I encountered an error creating the event: {str(e)}"

# Tool 3: Smart meeting details extraction (for testing/debugging)
def extract_details_tool(input_str):
    try:
        details = extract_meeting_details(input_str)
        return f"Extracted details: {json.dumps(details, indent=2)}"
    except Exception as e:
        return f"Error extracting details: {str(e)}"

# Tools the agent can call
tools = [
    Tool(
        name="Check Calendar", 
        func=check_avail_tool, 
        description="Check upcoming calendar events and availability. Use this when user asks about their schedule or free time."
    ),
    Tool(
        name="Create Event", 
        func=create_event_tool, 
        description="Create a new calendar event with intelligent parsing. Can extract meeting titles, dates, times, and durations from natural language. Handles complex requests like 'Schedule Team Meeting with John tomorrow at 3 PM for 90 minutes'."
    ),
    Tool(
        name="Extract Meeting Details", 
        func=extract_details_tool, 
        description="Extract and show meeting details from user input for debugging purposes."
    )
]

# Initialize main LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=api_key)

# Create agent with enhanced instructions
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    agent_kwargs={
        "prefix": """You are a professional AI calendar assistant with advanced natural language understanding. 
        You can:
        - Check calendar availability and show upcoming events
        - Create calendar events with intelligent parsing of titles, dates, times, and durations
        - Understand complex requests like "Schedule Team Meeting with John tomorrow at 3 PM for 90 minutes"
        - Extract meeting details from casual conversation
        
        When creating events, you can understand:
        - Meeting titles from context
        - Date and time expressions in natural language
        - Meeting durations when specified
        - Additional notes or details
        
        Always confirm important details with the user and be conversational and helpful."""
    }
)