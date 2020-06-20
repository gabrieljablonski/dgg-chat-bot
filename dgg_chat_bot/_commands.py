import logging
from typing import Union, Callable, Dict, Set, AnyStr
from dgg_chat.messages import ChatMessage, Whisper, EventTypes

from .exceptions import (
    CommandDescriptionTooLongError,
    DuplicateCommandError,
    InvalidMessageError,
    InvalidCommandError,
    InvalidCommandArgumentsError,
    UnknownCommandError,
)
from ._utils import (
    get_arity,
    sanitize_docs,
    call_with_typed_args,
    last_argument_is_of_type,
)


Message = Union[ChatMessage, Whisper]


class Handler:
    MAX_DESCRIPTION_LENGTH = 400

    def __init__(self, f: Callable, optional_args=False):
        self._f = f
        self.description = f.__doc__ or 'No description.'
        self.optional_args = optional_args

        self.description = sanitize_docs(self.description)
        if len(self.description) > self.MAX_DESCRIPTION_LENGTH:
            raise CommandDescriptionTooLongError(self.description)

    def __call__(self, raw_message: Message, *args):
        exp_raw = self.expects_raw_message
        actual_arity = self.arity - exp_raw

        if not actual_arity:
            if exp_raw:
                return self._f(raw_message)
            return self._f()

        args = list(args)

        if len(args) < actual_arity:
            # add empty strings to args to match the handler arity
            diff = actual_arity - len(args)
            args.extend('' for _ in range(diff))

        if len(args) > actual_arity:
            # extra arguments are clumped as the last one
            # (second to last if expects raw message)
            split = actual_arity - 1
            args, remaining = args[:split], ' '.join(args[split:])
            args.append(remaining)

        if exp_raw:
            args.append(raw_message)

        try:
            return call_with_typed_args(
                self._f, *args, optional_args=self.optional_args
            )
        except ValueError:
            raise InvalidCommandArgumentsError('invalid arguments')

    @property
    def arity(self):
        return get_arity(self._f)

    @property
    def expects_raw_message(self):
        return last_argument_is_of_type(self._f, Message)


class Command:
    def __init__(self, handler: Handler, keyword, *aliases):
        self._handler = handler
        self._keyword = keyword.lower()
        self._aliases = set(a.lower() for a in aliases)

    def __repr__(self):
        return f"Command(keyword='{self._keyword}', aliases={self._aliases})"

    @property
    def keyword(self):
        return self._keyword

    @property
    def aliases(self):
        return self._aliases

    @property
    def handler(self):
        return self._handler

    def is_alias(self, alias):
        return alias in self._aliases

    def add_alias(self, alias):
        self._aliases.add(alias)


class Commands:
    def __init__(self, command_prefix):
        self.command_prefix = command_prefix
        self._commands: Dict[Keyword, Command] = {}
        self._on_regular_message: Callable = None
        self._on_unknown_command: Callable = None
        self._on_invalid_arguments: Callable = None
        self._on_fail: Callable = None
        self._before_commands: Set[Callable] = set()
        self._after_commands: Set[Callable] = set()

    @property
    def on_regular_message(self):
        return self._on_regular_message

    @on_regular_message.setter
    def on_regular_message(self, f):
        # just in case restrictions are needed in the future
        self._on_regular_message = f

    @property
    def on_unknown_command(self):
        return self._on_unknown_command

    @on_unknown_command.setter
    def on_unknown_command(self, f):
        # just in case restrictions are needed in the future
        self._on_unknown_command = f

    @property
    def on_invalid_arguments(self):
        return self._on_invalid_arguments

    @on_invalid_arguments.setter
    def on_invalid_arguments(self, f):
        # just in case restrictions are needed in the future
        self._on_invalid_arguments = f

    @property
    def on_fail(self):
        return self._on_fail

    @on_fail.setter
    def on_fail(self, f):
        # just in case restrictions are needed in the future
        self._on_fail = f

    @property
    def all_aliases(self):
        aliases = []
        for keyword, command in self._commands.items():
            aliases.append(keyword)
            aliases.extend(command.aliases)
        return aliases

    def get_root(self, alias):
        if command := self._commands.get(alias):
            return command
        for command in self._commands.values():
            if command.is_alias(alias):
                return command

    def add_before_commands(self, f):
        self._before_commands.add(f)
        return f

    def add_after_commands(self, f):
        self._after_commands.add(f)
        return f

    def add(
        self, f, keyword, *aliases,
        override=False,
        optional_args=False,
    ):
        for alias in aliases:
            if self.get_root(alias):
                raise DuplicateCommandError(alias)

        if self.get_root(keyword) and not override:
            raise DuplicateCommandError(keyword)

        handler = Handler(f, optional_args)
        command = Command(handler, keyword, *aliases)
        self._commands[keyword] = command

    def handle(self, message: Message):
        command = message.content.strip()

        if not command.startswith(self.command_prefix):
            if self._on_regular_message:
                return self._on_regular_message(message)
            raise InvalidCommandError(command)

        keyword, *args = command.lstrip(self.command_prefix).strip().split(' ')

        if not (command := self.get_root(keyword.lower())):
            if self._on_unknown_command:
                return self._on_unknown_command(keyword)
            raise UnknownCommandError(command)

        try:
            try:
                for h in self._before_commands:
                    h(message, command.keyword, *args)
                command.handler(message, *args)
            except InvalidCommandArgumentsError as e:
                logging.debug(f"invalid arguments: {command}, {args}. Error: {e}")
                self._on_invalid_arguments(command, str(e))
                raise e
            except Exception as e:
                logging.debug(f"something went wrong: {command}, {args}. Error: {e}")
                self._on_fail(command, str(e))
                raise e
        except Exception as e:
            for h in self._after_commands:
                h(e, message, command.keyword, *args)
