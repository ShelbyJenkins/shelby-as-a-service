#region
import os
import random
import logging
import traceback
import sys

import discord
from discord.ext import commands

from agents.logger_agent import LoggerAgent
from agents.async_shelby_agent import ShelbyAgent

# For local use. When deployed as container there is no .env and enviroment vars are loaded from github secrets at deploy
from dotenv import load_dotenv
load_dotenv()
bot_token = os.getenv('DISCORD_TOKEN')
channel_id = int(os.environ['DISCORD_CHANNEL_ID'])

log_agent = LoggerAgent('discord_sprite', 'discord_sprite.log', level='INFO')

intents = discord.Intents.default()
intents.guilds = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)
#endregion

# This checks if the specified channel_id exists in the server the bot is added to and leaves if it doesn't exist
# This prevents the bot from being added to servers that aren't approved
@bot.event
async def on_guild_join(guild):
    if not any(channel.id == channel_id for channel in guild.channels):
            log_agent.print_and_log(f'Leaving guild {guild.name} (ID: {guild.id}) due to missing channel.')
            await guild.leave()
    channel = bot.get_channel(channel_id)
    await channel.send(format_message(welcome_message, get_random_animal()))
            
# App start up actions
@bot.event
async def on_ready():
    for guild in bot.guilds:
        if not any(channel.id == channel_id for channel in guild.channels):
            log_agent.print_and_log(f'Leaving guild {guild.name} (ID: {guild.id}) due to missing channel.')
            await guild.leave()
        
    log_agent.print_and_log(f'Bot has logged in as {bot.user.name} (ID: {bot.user.id})')
    log_agent.print_and_log('------')
    channel = bot.get_channel(channel_id)

    await channel.send(format_message(welcome_message, get_random_animal()))

# On messages in the server. The bot should be configured in discord developer portal to only recieve messages where it's tagged,
# but in the case it's configured to recieve all messages we cover for this case as well
@bot.event
async def on_message(message):
    log_agent.print_and_log(f'Message received: {message.content} (From: {message.author.name})')
    if bot.user.mentioned_in(message):
        # Don't respond to ourselves
        if message.author == bot.user.id:
            return
        if "rabbit" in message.content.lower():
            await message.channel.send(f'No, I will not tell you about the rabbits, <@{message.author.id}>,.')
            return
        # Must be in the approved channel
        if message.channel.id != channel_id:
            return
        
        request = message.content.replace(f'<@{bot.user.id}>', '').strip()
    
        # If question is too short
        if len(request.split()) < 4:
            await message.channel.send(format_message(short_message, message.author.id))
            return
        
        # Create thread
        thread = await message.create_thread(name=f"{get_random_animal()} {message.author.name}'s request", auto_archive_duration=60)

        await thread.send(message_start)
        
        try:
            request_response = await agent.run_request(request)
        except Exception as e:
            tb = traceback.format_exc()
            log_agent.print_and_log(f"An error occurred: {str(e)}. Traceback: {tb}")
            await thread.send(f"An error occurred: {str(e)}. Traceback: {tb}")
            return 
        
        # Parse for discord and then respond
        parsed_reponse = parse_discord_markdown(request_response)
        log_agent.print_and_log(f'Parsed output: {parsed_reponse})')
        await thread.send(parsed_reponse)

        await thread.send(format_message(message_end, request_response['llm']))

def parse_discord_markdown(request_response):
    # Start with the answer text
    markdown_string = f"{request_response['answer_text']}\n\n"

    # Add the sources header if there are any documents
    if request_response['documents']:
        markdown_string += "**Sources:**\n"

        # For each document, add a numbered list item with the title and URL
        for doc in request_response['documents']:
            markdown_string += f"[{doc['doc_num']}] **{doc['title']}**: <{doc['url']}>\n"
    else:
        markdown_string += "No related documents found.\n"
  
    return markdown_string

# Very important
def get_random_animal():
    animals_txt_path = os.path.join('data', 'animals.txt')
    with open(animals_txt_path, 'r') as file:
        animals = file.readlines()
    return random.choice(animals).strip().lower()

def format_message(template, var=None):
    if var:
        return template.format(var)
    return template.format

welcome_message = 'ima tell you about the {}.'
short_message = '<@{}>, brevity is the soul of wit, but not of good queries. Please provide more details in your request.'
message_start = 'Running request... relax, chill, and vibe a minute.'
message_end = 'Generated by: {}\nMemory not enabled. Has no knowledge of past or current queries.\nFor code see https://github.com/ShelbyJenkins/shelby-as-a-service.'


if __name__ == "__main__":
    agent = ShelbyAgent()
    # Runs the bot through the asyncio.run() function built into the library
    bot.run(bot_token)


