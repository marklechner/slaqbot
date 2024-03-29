import logging

logging.basicConfig(level=logging.INFO)
import os
import json
import asyncio
import concurrent.futures
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from dotenv import load_dotenv
load_dotenv()
SLACK_BOT_TOKEN = os.environ['SLACK_BOT_TOKEN']
SLACK_APP_TOKEN = os.environ['SLACK_APP_TOKEN']
with open('answer_blocks.json', 'r') as f:
    blocks = f.read()
ANSWER_BLOCKS_TEMPLATE = blocks

app = AsyncApp(token=SLACK_BOT_TOKEN)

from openai import OpenAI
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
ASSISTANT_ID = os.environ["ASSISTANT_ID"]

# Handle non-slash command events
@app.event("app_mention")
async def event_test(event, say):
    await say(f"Hi there, <@{event['user']}>! Please use the /faq command to ask me a question.")

@app.event("message")
async def handle_message_events(event, say):
    await say(f"Hi there, <@{event['user']}>! Please use the /faq command to ask me a question.")

# Handle proper slash command events
@app.command("/faq")
async def faq_command(ack, body):
    logging.info(f"User {body['user_name']} called /faq with payload \"{body['text']}\"")
    if not body['text'].strip():  # Check if the command was called with no additional text
        response = "Please provide a question after the /faq command."
        await ack(f"{response}")
    else:
        asyncio.create_task(handle_faq(body))
        response = f"*Your question:* _{body['text']}_ \nLet me see if I can answer that..."
        await ack(f"{response}")

# Function to take slack message, get an answer from OpenAI and send DM back to user with the answer
async def handle_faq(body):
    response = await ask_llm(body['text'])
    await send_dm(body['user_id'], body['channel_id'],body['text'], response)

# Function to get answer to question from OpenAI assistant
async def ask_llm(payload):
    loop = asyncio.get_event_loop()

    with concurrent.futures.ThreadPoolExecutor() as pool:
        client = OpenAI()
        thread = await loop.run_in_executor(pool, client.beta.threads.create)
        message = await loop.run_in_executor(pool, lambda: client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=payload
        ))
        run = await loop.run_in_executor(pool, lambda: client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID,
        ))
        # TODO: once assistant api is out of beta hopefully there is a better way to figure out when the run is completed
        await asyncio.sleep(2)
        while True:
            run = await loop.run_in_executor(pool, lambda: client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            ))
            if run.status == 'completed':
                break
            await asyncio.sleep(3)
        messages = await loop.run_in_executor(pool, lambda: client.beta.threads.messages.list(
            thread_id=thread.id
        ))
        response = (messages.data[0].content[0].text.value)
        return response

# Function to send ephemeral message back to user with the answer
async def send_dm(user_id, channel_id, question, response):
        # substitute question and answer into blocks template
        blocks = str(ANSWER_BLOCKS_TEMPLATE).replace("{question}", question).replace("{answer}", response)
        blocks = json.loads(blocks)
        await app.client.chat_postEphemeral(
            blocks=blocks,
            user=user_id,
            channel=channel_id,
            text="Here is what I found in the FAQ: _response_"
        )


async def main():
    handler = AsyncSocketModeHandler(app, SLACK_APP_TOKEN)
    await handler.start_async()


if __name__ == "__main__":
    asyncio.run(main())
