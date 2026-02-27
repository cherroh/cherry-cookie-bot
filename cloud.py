"""
Cherry Cookie Landmine Bot for Discord
bot.py is the cloud version of the bot, intended to be deployed on Render

Author: cherrow
This bot randomly times out users who send messages in a server, simulating a "landmine" effect.
The chance of triggering the landmine is configurable, and users are put on a cooldown to prevent abuse.
The bot also logs timeout events in a specified channel.
"""

import os
import random
import discord
from dotenv import load_dotenv
from datetime import datetime, timedelta, UTC
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import asyncio

# Simple HTTP server so Render sees this as a web service
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

def start_server():
    server = HTTPServer(("0.0.0.0", 8080), HealthCheck)
    server.serve_forever()

# Run HTTP server in a background thread
threading.Thread(target=start_server, daemon=True).start()

# Load the bot token from the .env file
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Ensure the token is available
if TOKEN is None:
    raise ValueError("Bot token not found in environment variables.")

# Configuration constants
LANDMINE_CHANCE = 0.001 # 0.1% chance to explode, should be 0.001
LANDMINE_DURATION = 60 # in seconds
COOLDOWN_SECONDS = 5 # prevents spam-trigger abuse
LOG_CHANNEL_NAME = "timeout-hall-of-shame"  # logging channel, change this to your desired channel name or set to None to disable logging
GIF_URL = "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExemFyaW1zdGpsZnR1cG51aDR0dGF4bHplaHQ4cmRxd2QwOGswOXR4bCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/hvGKQL8lasDvIlWRBC/giphy.gif" # GIF of landmine

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

# Cooldown tracking for users to prevent spam-trigger abuse
user_cooldowns = {}

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

# Main event handler for incoming messages
@client.event
async def on_message(message):
    # Ignore messages from bots
    if message.author.bot:
        return
    
    # Only operate in guilds (servers), ignore DMs
    if message.guild is None:
        return

    # Get the current time in UTC for cooldown tracking
    now = datetime.now(UTC)

    # Check if the user is on cooldown
    last_trigger = user_cooldowns.get(message.author.id)
    if last_trigger and (now - last_trigger).total_seconds() < COOLDOWN_SECONDS:
        return

    # Check if the landmine should trigger
    if random.random() < LANDMINE_CHANCE:
        try:
            # Get the member object for the user who sent the message
            member = message.author

            # Attempt to timeout the user
            await member.timeout(
                timedelta(seconds=LANDMINE_DURATION),
                reason="Random Cherry Cookie landmine"
            )

            # Update the cooldown for the user
            user_cooldowns[message.author.id] = now

            # Calculate the chance percentage for display
            chance_percent = LANDMINE_CHANCE * 100
            chance_str = f"{chance_percent:g}"

            # Send a message to the channel about the landmine trigger
            await message.channel.send(
                f"💥 {message.author.mention} stepped on a landmine and has been timed out for 1 minute! "
                f"({chance_str}% chance of occurring per message sent btw)"
            )

            # Send the landmine GIF
            await message.channel.send(GIF_URL)

            # Log the event in the specified log channel, if it exists
            log_channel = discord.utils.get(
                message.guild.text_channels,
                name=LOG_CHANNEL_NAME
            )

            # Log the timeout event in the log channel
            if log_channel:
                await log_channel.send(
                    f"🚨 {message.author} triggered a landmine in {message.channel.mention} and got a timeout!"
                )

        # Handle any exceptions that occur during the timeout process
        except Exception as e:
            print("Timeout failed:", e)

# Start the bot using the token from the environment variable
async def start_bot():
    await asyncio.sleep(5)

    for attempt in range(5):
        try:
            await client.start(TOKEN)
            break
        except Exception as e:
            print(f"Login attempt {attempt + 1} failed:", e)
            await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(start_bot())
