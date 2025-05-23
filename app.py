import base64
import streamlit as st
import urllib.request
import json
import os
import ssl
from dotenv import load_dotenv
from io import StringIO  # Added for reading file contents

# Load environment variables
load_dotenv()
AZURE_ENDPOINT_KEY = os.environ['AZURE_ENDPOINT_KEY']

def allowSelfSignedHttps(allowed):
    # bypass the server certificate verification on the client side
    if allowed and not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
        ssl._create_default_https_context = ssl._create_unverified_context

def main():
    
    allowSelfSignedHttps(True)

    left_co, cent_co, last_co = st.columns(3)
    with cent_co:
        st.image("logo.png", width=200)
    
    st.markdown("<h1 style='text-align: center; color: #005AD2; marginTop: -60px'>Poly Phone Error Buddy</h1>", unsafe_allow_html=True)
    
    # Description
    st.markdown(
        """
        <p style='text-align: center; font-size: 24px; color: #333;'>
        This tool helps you troubleshoot extensive poly-phone error logs by providing a summary of issues and solutions.
        </p>
        """, 
        unsafe_allow_html=True
    )

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display chat history
    for interaction in st.session_state.chat_history:
        if interaction["inputs"]["question"]:
            with st.chat_message("user"):
                st.write(interaction["inputs"]["question"])
        if interaction["outputs"]["answer"]:
            with st.chat_message("assistant"):
                st.write(interaction["outputs"]["answer"])

    # React to user input
    user_input = st.chat_input("Ask me anything...")

    # File uploader (placed under the message input field)
    uploaded_file = st.file_uploader("Upload a log file", type=["txt", "log"])
    
    if uploaded_file is not None:
        # Read file as string and set it as user input
        byte_data = uploaded_file.getvalue()
        encoded_data = base64.b64encode(byte_data)

        # st.chat_message("user").markdown(string_data) DELETED

        # Optionally, append the file content to the chat history
        st.session_state.chat_history.append(
            {"inputs": {"base64_file": str(encoded_data, 'utf-8')},
             "outputs": {"answer": "Uploaded log file contents."}}
        )

        # Treat the uploaded file content as user input
        user_input = str(encoded_data, 'utf-8')

    # Process user input if it exists
    if user_input:
        # Display user message in chat message container
        st.chat_message("user").markdown(user_input)
        
        # Query API
        data = {"chat_history": st.session_state.chat_history, 'question': user_input}
        body = json.dumps(data).encode('utf-8')
        url = 'https://promptflowpreloadedknowledge.westeurope.inference.ml.azure.com/score'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {AZURE_ENDPOINT_KEY}',
            'azureml-model-deployment': 'promptflowpreloadedknowledge-3'
        }
        req = urllib.request.Request(url, body, headers)

        try:
            response = urllib.request.urlopen(req)
            response_data = json.loads(response.read().decode('utf-8'))

            # render
            with st.chat_message("assistant"):
                st.markdown(response_data['answer']) 

            # add user input to chat history
            st.session_state.chat_history.append(
                {"inputs": {"question": user_input},
                 "outputs": {"answer": response_data['answer']}}
            )

        except urllib.error.HTTPError as error:
            st.error(f"The request failed with status code: {error.code}")
            st.text(error.read().decode("utf8", 'ignore'))



if __name__ == "__main__":
    main()