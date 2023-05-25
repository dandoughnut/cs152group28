# bot.py
import discord
from discord.ext import commands
import os
import json
import logging
import re
import requests
from report import Report
import pdb

# Set up logging to the console
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# There should be a file called 'tokens.json' inside the same folder as this file
token_path = 'tokens.json'
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
    tokens = json.load(f)
    discord_token = tokens['discord']


class ModBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='.', intents=intents)
        self.group_num = None
        self.mod_channels = {}  # Map from guild to the mod channel id for that guild
        self.reports = {}  # Map from user IDs to the state of their report

    ############################################## Discord Method Overloads ##############################################
    async def on_ready(self):
        '''
        Called when the client is done preparing the data received from Discord. Usually after login is successful and the Client.guilds and co. are filled up.
        '''
        print(f'{self.user.name} has connected to Discord! It is these guilds:')
        for guild in self.guilds:
            print(f' - {guild.name}')
        print('Press Ctrl-C to quit.')

        # Parse the group number out of the bot's name
        match = re.search('[gG]roup (\d+) [bB]ot', self.user.name)
        if match:
            self.group_num = match.group(1)
        else:
            raise Exception(
                "Group number not found in bot's name. Name format should be \"Group # Bot\".")

        # Find the mod channel in each guild that this bot should report to
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == f'group-{self.group_num}-mod':
                    self.mod_channels[guild.id] = channel

    async def on_message(self, message):
        '''
        This function is called whenever a message is sent in a channel that the bot can see (including DMs). Currently the bot is configured to only handle messages that are sent over DMs or in your group's "group-#" channel.
        '''
        # Ignore messages from the bot
        if message.author.id == self.user.id:
            return

        # Check if this message was sent in a server ("guild") or if it's a DM
        if message.guild:
            await self.handle_channel_message(message)
        else:
            await self.handle_dm(message)

    async def on_raw_reaction_add(self, message):
        '''
        Called when a message has a reaction added.
        '''
        # Ignore reactions from the bot
        if message.user_id == self.user.id:
            return

        print(message)
        # Sample: <RawReactionActionEvent message_id=1110666813022425098 user_id=1098756525004173402 channel_id=1103033289041789052 guild_id=1103033282779676743 emoji=<PartialEmoji animated=False name='👍' id=None> event_type='REACTION_ADD' member=<Member id=1098756525004173402 name='stevengo' discriminator='1519' bot=False nick=None guild=<Guild id=1103033282779676743 name='CS 152 - Sp23' shard_id=0 chunked=False member_count=235>>>

    ####################################################### Handlers #####################################################

    async def handle_dm(self, message):
        # Handle a help message
        if message.content == Report.HELP_KEYWORD:
            reply = "\n\nUse the `report` command to begin the reporting process.\n"
            reply += "Use the `cancel` command to cancel the report process.\n"
            await message.channel.send(reply)
            return

        author_id = message.author.id
        responses = []

        # Only respond to messages if they're part of a reporting flow
        if author_id not in self.reports and not message.content.startswith(Report.START_KEYWORD):
            return

        # If we don't currently have an active report for this user, add one
        if author_id not in self.reports:
            self.reports[author_id] = Report(self)

        # Let the report class handle this message; forward all the messages it returns to us
        messagesFromReport = await self.reports[author_id].handle_message(message)
        # Send the bot's response message
        responseText = ""
        for m in messagesFromReport["messages"]:
            responseText += m + "\n"
        botResponse = await message.channel.send(responseText)
        # Add any reactions to the bot response
        for r in messagesFromReport["reactions"]:
            await botResponse.add_reaction(r)

        # If the report is complete or cancelled, remove it from our map
        if self.reports[author_id].report_complete():

            # Send the completed report to the mod channel
            # TODO: don't do this if the report was cancelled...
            reportedMessage = self.reports[author_id].message

            await self.mod_channels[reportedMessage.guild.id].send(f'{message.author.mention} has reported this message from {reportedMessage.author.mention}: ```{reportedMessage.author.name}: {reportedMessage.content}``` \n See the message in context: {reportedMessage.jump_url}')

            # Remove report from map
            self.reports.pop(author_id)

    async def handle_channel_message(self, message):
        # Only handle messages sent in the "group-#" channel
        if not message.channel.name == f'group-{self.group_num}':
            return

        # Forward the message to the mod channel
        mod_channel = self.mod_channels[message.guild.id]
        await mod_channel.send(f'Forwarded message:\n{message.author.name}: "{message.content}"')

        scores = self.eval_text(message.content)
        await mod_channel.send(self.code_format(scores))

    ################################################# Helper Functions ##################################################

    def eval_text(self, message):
        ''''
        TODO: Once you know how you want to evaluate messages in your channel, 
        insert your code here! This will primarily be used in Milestone 3. 
        '''
        return message

    def code_format(self, text):
        ''''
        TODO: Once you know how you want to show that a message has been 
        evaluated, insert your code here for formatting the string to be 
        shown in the mod channel. 
        '''
        return "Evaluated: '" + text + "'"


client = ModBot()
client.run(discord_token)
