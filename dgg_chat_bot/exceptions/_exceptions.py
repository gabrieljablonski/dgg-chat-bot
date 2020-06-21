class CommandDescriptionTooLongError(Exception):
    """
    Raised when the command description (via `f.__doc__`) is too long.
    """


class DuplicateCommandError(Exception):
    """
    Raised when a keyword or alias has already been used for a command.
    """

    def __init__(self, alias):
        msg = f"`{alias}` was already used as a keyword or alias for a command. use `override=True` to override it"
        super().__init__(msg)


class InvalidCommandError(Exception):
    """
    Raised when the message does not start with command prefix.
    """


class UnknownCommandError(Exception):
    """
    Raised when the command is not recognized.
    """


class InvalidCommandArgumentsError(Exception):
    """
    Raised when the arguments used for the command were invalid.
    """


class HandlerFailedError(Exception):
    pass
