import streamlit as st
import requests
import os
import json

st.set_page_config(page_title="Calendar AI Agent", page_icon="🚀")
st.title("📅 Conversational Calendar Agent")
st.caption("Your personal AI assistant for booking appointments on Google Calendar.")

BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000") 

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! How can I help you with your calendar today? You can ask me to check for available slots or book an appointment."}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What would you like to do?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")

        try:
            payload = {
                "question": prompt
            }

            response = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=300)
            response.raise_for_status()

            full_response = response.json().get("response", "Sorry, I encountered an error.")

        except requests.exceptions.RequestException as e:
            full_response = f"Error: Could not connect to the backend. Please make sure it's running. Details: {e}"
        except json.JSONDecodeError:
            full_response = "Error: Failed to decode the response from the backend. The response was not valid JSON."
        except Exception as e:
            full_response = f"An unexpected error occurred: {e}"

        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
