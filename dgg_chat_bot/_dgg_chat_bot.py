import logging
from time import sleep
from dgg_chat import DGGChat

from .exceptions import InvalidMessageError, AnonymousConnectionError
from ._commands import Commands, Message, Whisper
from ._utils import parametrized_decorator_method, enclose


class DGGChatBot:
    def __init__(self, auth_token=None, command_prefix='!', extra_help=''):
        """
        Parameters
        ----------
        `auth_token` : `str`

            an authentication token for a dgg account.
            can be created at `https://www.destiny.gg/profile/developer`.       

        `command_prefix` : `str`

            the character sequence at the start of a message
            to indicate it's a command.
            `"!"` by default.

        `extra_help` : `str`

            extra details to be put at the end of the default help function reply.
        """
        self._auth_token = auth_token
        self.command_prefix = command_prefix
        self.extra_help = extra_help
        self._last_whisper_received = None

        self._commands = Commands(command_prefix)

        self._chat = DGGChat(auth_token)

        self._setup_default_commands()
        self._setup_chat_handlers()

    @property
    def auth_token(self):
        return self._auth_token

    @property
    def commands(self):
        return self._commands

    @property
    def chat(self):
        return self._chat

    def _setup_default_commands(self):
        @self.on_command('help', 'h', 'commands', optional_args=True)
        def on_help(cmd):
            """documentation set below"""

            if cmd:
                if not (command := self._commands.get_root(cmd)):
                    return self.reply('The command `{cmd}` was not found.')
                aliases = ', '.join(enclose(command.aliases, '"')) or 'none'
                desc = command.handler.description
                msg = f'"{self.command_prefix}{command.keyword}" (aliases: {aliases}) -> {desc}'
                return self.reply(msg)

            commands = ', '.join(enclose(self._commands.all_aliases, '"'))
            if not commands:
                msg = 'No commands are available ☹.'
                return self.reply(msg)
            msg = f'Available commands: {commands}. For more info about a specific command, try "{self.command_prefix}help <command>". {self.extra_help}'
            return self.reply(msg)

        # setting manually since formatting is needed
        on_help.__doc__ = f"""
        The command you're using! 
        Use it to get info about available commands.
        Examples: "{self.command_prefix}help", "{self.command_prefix}help <command>".
        """

        @self.on_unknown_command
        def on_unknown_command(command):
            msg = f"""Sorry, I don't know that one 🤔. Try "{self.command_prefix}help"."""
            self.reply(msg)

        @self.on_regular_message
        def on_regular_message(message: Message):
            msg = f"""Hey, {message.user.nick}! I'm a bot 🤖 *beep* *boop*. To check what I can do, try "{self.command_prefix}help"."""
            self.reply(msg)

        @self.on_invalid_arguments
        def on_invalid_arguments(command, error_message=''):
            keyword = command.keyword
            error_message = f" Error message: {error_message}." if error_message else ''
            msg = f"""I don't think this you how you use that 🤔.{error_message} Try "{self.command_prefix}help {keyword}" for more info."""
            self.reply(msg)

        @self.on_fail
        def on_fail(command, error_message=''):
            error_message = f" Error message: {error_message}." if error_message else ''
            msg = f"""Something went wrong while processing your command.{error_message}"""
            self.reply(msg)

    def _setup_chat_handlers(self):
        # @self._chat.on_chat_message
        @self._chat.on_whisper
        def on_whisper(whisper: Whisper):
            self._last_whisper_received = whisper
            self._commands.handle(whisper)

    def connect(self):
        self._chat.connect()

    def disconnect(self):
        self._chat.disconnect()

    def run_forever(self):
        self._chat.run_forever()

    def on_regular_message(self, f):
        self._commands.on_regular_message = f
        return f

    def on_unknown_command(self, f):
        self._commands.on_unknown_command = f
        return f

    def on_invalid_arguments(self, f):
        self._commands.on_invalid_arguments = f
        return f

    def on_fail(self, f):
        self._commands.on_fail = f
        return f

    def before_commands(self, f):
        return self._commands.add_before_commands(f)

    def after_commands(self, f):
        return self._commands.add_after_commands(f)

    @parametrized_decorator_method
    def on_command(
        self, f, keyword, *aliases,
        override=False,
        optional_args=False,
    ):
        if not self._auth_token:
            raise AnonymousConnectionError(
                'setting command handlers is not very useful without a connection'
            )

        self._commands.add(
            f, keyword, *aliases,
            override=override,
            optional_args=optional_args
        )
        return f

    def reply_multiline(self, messages):
        """
        Replies to the last whisper received with multiple messages.
        Use sparingly, since you're likely to get throttled.
        """
        for m in messages:
            self.reply(m)

    def reply(self, message):
        """
        Replies to the last whisper received.
        """
        if not self._chat.message_is_valid(message):
            raise InvalidMessageError(message)
        user = self._last_whisper_received.user.nick
        self._chat.send_whisper(user, message)
