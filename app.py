import discord
from discord.ext import commands, tasks
import requests
import json
import re
import asyncio

endpoint = ""
api_key = ""
TOKEN = ""

def extract_json(text):
    json_regex = re.compile(r'\{.*\}')
    matches = json_regex.findall(text)
    if not matches:
        return False

    json_data = matches[0]
    return json.loads(json_data)

def analyse(message):
    print(message)
    headers = {
        'authorization': f'Bearer {api_key}',
    }

    json_data = {
        'model': 'mixtral-8x7b-32768',
        'messages': [
            {
                'role': 'user',
                'content': f"""
Analyze the input message to determine if it contains known scam links or patterns typically associated with fraudulent messages. If the input message is identified as containing scam content, respond with a JSON object {{"scam": true}}. If the input message does not contain scam content, respond with a JSON object {{"scam": false}}.
Do not detect as scam link, if it's from genuine source like google.com, youtube.com, discord.com, etc. Always mark gift links as scam.

Input Message: {message}

Just respond with json object. Nothing else.
    """,
            },
        ],
        'temperature': 0.5,
        'max_tokens': 1024,
        'top_p': 1,
        'stop': None,
        'stream': False,
    }

    response = requests.post(f'https://{endpoint}/v1/chat/completions', headers=headers, json=json_data)
    print(response.json())
    response = (response.json()["choices"][0]["message"]["content"])
    return extract_json(response)

url_regex = re.compile(r'https?://(?:www\.)?(?:[a-zA-Z0-9-]+\.?)+[a-zA-Z]{2,}(?:/[^\s]*)?')

intents = discord.Intents.all()
client = commands.Bot(command_prefix="!", intents=intents)

async def action(message):
    user = message.author
    embed = discord.Embed(
        description=f"⚠️ You have been found using a scam/phishing link. Please refrain from doing so.",
        color=0xFF0000
    )
    user_reply = await message.reply(embed=embed)
    await asyncio.sleep(30)
    try:
        await message.delete()
    except discord.errors.NotFound:
        pass
    
    try:
        await user_reply.delete()
    except discord.errors.NotFound:
        pass
    
    return

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    # Avoid the bot responding to its own messages
    if message.author == client.user:
        return

    # Check if the message contains a URL
    if url_regex.search(message.content):
        if analyse(message.content)["scam"] == True:
            print(message.content)
            await action(message)
    return        

# Start the bot
client.run(TOKEN)
