# Description: This script can be used to setup the OpenAI assistant and obtain value for the
# ASSISTANT_ID variable required to be in .env

import os
from dotenv import load_dotenv
load_dotenv()
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

from openai import OpenAI
client = OpenAI()

# Create an assistant
def create_assistant(client):
    my_assistant = client.beta.assistants.create(
        instructions="You are an internal facing support chatbot for employees calling you via Slack. Use the information provided in the \"FAQ.yaml\" file which contains all FAQ articles to answer support-related questions.\nAlways reply with a friendly tone of voice to the user in a brief format and please only provide factual information to questions, by sticking to the contents of FAQ.yaml. If nothing relevant found, explain to the user, how this information is missing and they should work with the relevant team to update the body of knowledge accordingly.",
        name="Slack FAQ Bot",
        tools=[{"type": "retrieval"}],
        model="gpt-3.5-turbo-1106",
        file_ids=["file-abc123"],
    )
    print(my_assistant)

# Create a file
def create_file(client):
    assistant_file = client.beta.assistants.files.create(
    assistant_id="asst_abc123",
    file_id="file-abc123"
    )
    print(assistant_file)

# List assistants
def list_assistants(client):
    my_assistants = client.beta.assistants.list(
        order="desc",
        limit="20",
    )
    print(my_assistants.data)

# Main program
if __name__ == "__main__":
    #create_assistant(client)
    #create_file(client)
    list_assistants(client)
