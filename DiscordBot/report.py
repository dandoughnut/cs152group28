from enum import Enum, auto
import discord
import re


class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    MESSAGE_IDENTIFIED = auto()
    REPORT_COMPLETE = auto()


class Report:
    START_KEYWORD = "report"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    def __init__(self, client):
        self.state = State.REPORT_START
        self.client = client
        self.message = None

    async def handle_message(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to get you started and give you a model for working with Discord.
        Returns a dict with keys "messages" and "reactions". Corresponding value is an array of strings of that type.
        '''

        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REPORT_COMPLETE
            return {"messages": ["Report cancelled."], "reactions": []}

        if self.state == State.REPORT_START:
            reply = "\nThank you for starting the reporting process. "
            reply += "Say `help` at any time for more information.\n\n"
            reply += "Please copy paste the link to the message you want to report.\n"
            reply += "You can obtain this link by right-clicking the message and clicking `Copy Message Link`."
            self.state = State.AWAITING_MESSAGE
            return {"messages": [reply], "reactions": []}

        # We don't yet have a message
        if self.state == State.AWAITING_MESSAGE:
            # Do some error checking...
            # Parse out the three ID strings from the message link
            m = re.search('/(\d+)/(\d+)/(\d+)', message.content)
            if not m:
                return {"messages": ["I'm sorry, I couldn't read that link. Please try again or say `cancel` to cancel."], "reactions": []}

            guild = self.client.get_guild(int(m.group(1)))
            if not guild:
                return {"messages": ["I cannot accept reports of messages from guilds that I'm not in. Please have the guild owner add me to the guild and try again, or say `cancel` to cancel."], "reactions": []}

            channel = guild.get_channel(int(m.group(2)))
            if not channel:
                return {"messages": ["It seems this channel was deleted or never existed. Please try again or say `cancel` to cancel."], "reactions": []}

            try:
                message = await channel.fetch_message(int(m.group(3)))
            except discord.errors.NotFound:
                return {"messages": ["It seems this message was deleted or never existed. Please try again or say `cancel` to cancel."], "reactions": []}

            # Begin the reporting flow: get information about the type of abuse
            self.state = State.MESSAGE_IDENTIFIED
            self.message = message
            return {
                "messages": ["You are reporting this message:", "```" + message.author.name + ": " + message.content + "```", "Why are you reporting this message? \n",
                             "💩 This message contains content that is inappropriate for this context and people shouldn't see it.",
                             "👿 This message is harassment, bullying, or generally mean or hurtful.",
                             "💳 I think that this is a spam message or a scam, not a real person genuinely trying to interact.",
                             "🔪 I think this message could lead to bad stuff happening offline.",
                             "✍️ None of these, some other reason.",
                             "🙅 I didn't mean to report this message! No action needed."],
                "reactions": ["💩", "👿", "💳", "🔪", "✍️", "🙅"]}

        # We have the message -- now begin acting on it!
        if self.state == State.MESSAGE_IDENTIFIED:
            return {"messages": ["idk!!"], "reactions": []}

        # Base case -- something has gone wrong if we reach this
        return {"messages": ["I'm sorry, something has gone wrong. Please report this error."], "reactions": ["😭"]}

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE
