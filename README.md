# DGG Chat Bot

A framework for building chat bots for the [destiny.gg](https://destiny.gg) chat. It allows you to register 
commands for when a user whispers you, so you can then reply with something useful.
Built with the [`dgg-chat`](https://github.com/gabrieljablonski/dgg-chat) package.

In case you want a more in-depth example, check out the [remind me bot](https://github.com/gabrieljablonski/dgg-remind-me).

## Installing

This package is available via pip (requires python 3.8).

```sh
pip install dgg-chat-bot
```

A (very) minimal working example (more details below):

```python
from dgg_chat_bot import DGGChatBot

bot = DGGChatBot("<dgg auth token>")

@bot.on_command('helloworld')
def hello_world():
    bot.reply('Hello World!')

bot.run_forever()
```

## How To Use

The `DGGChatBot` class runs the main event loop. It parses messages users sent to you for a command 
and invokes any functions registered. Registering a function to a command can be done with the 
`DGGChatBot().on_command()` decorator.

As it is with the `dgg-chat` package, all handlers are called synchronously, that is, a handler 
will only be called after the previous one finished its work. If you want to do time intensive tasks,
the asynchronous aspect has to be done manually. Native asynchronous support might be implemented in the future.

A more complete example can be found in the [`example.py`](./example.py) file.

## Registering Commands

When using the `on_command()` decorator, the first argument will be the keyword associated with 
that command, followed by any number of aliases. There's also `override` and `optional_args`, 
arguments explained later on.

It is enforced that the same alias cannot be used for multiple commands. Unless you set 
`override` to `True`, keywords also cannot be reused. `override` is specially useful to 
define your own `help` command, in case you don't like the [default one](./dgg_chat_bot/_dgg_chat_bot.py#L56).

```python
@bot.on_command('command', 'alias1', 'alias2')
def on_command():
    ...

@bot.on_command('help', 'h', override=True)
def custom_on_help():
    ...
```

### Defining A Command Handler

Command handlers can have any number of arguments. Arguments are defined as each
word that follows the command keyword in the message received, separated by spaces.
If the handler defines no arguments, everything after the keyword is ignored.
Example:

```python
@bot.on_command('command')
def on_command(arg1, arg2):
    # user invokes "!command abc 123"
    # arg1 = 'abc', arg2 = '123'
```

In case the command is invoked with more arguments than defined, all exceeding words are grouped as the last argument. 

If `optional_args` is set to `False` (default value), `InvalidCommandArgumentsError` exception is raised, 
and the `on_invalid_arguments()` special handler is called instead, which is explained further on. 

In case arguments received are less than expected, and `optional_args` is `True`, missing arguments are 
received as empty value (`''` or `0` for numeric arguments, as explained later). 

Examples:

```python
@bot.on_command('command', optional_args=True)
def on_command(arg1, arg2, multi_word_arg):
    # user invokes "!command arg1"
    # arg1 = 'arg1', other args equal to ''
    #
    # user invokes "!command 1 2 3 4 5 6"
    # arg1 = '1', arg2 = '2', and multi_word_arg = '3 4 5 6'

@bot.on_other_command('othercommand')
def on_other_command(arg1, arg2):
    # user invokes "!othercommand"
    # `InvalidCommandArgumentsError` is raised, and `on_invalid_arguments()` is called instead
```

#### Typed Arguments

Arguments can be set to expect specific types using [annotations](https://realpython.com/lessons/annotations/), 
specially useful when you want an argument to be an `int` or `float` (arguments are `str` by default). 

If the command is invoked using arguments of wrong type, `InvalidCommandArgumentsError` is raised and 
`on_invalid_arguments()` is called. 

The `Optional` annotation from the `typing` package can be used to selectively enforce certain arguments,
instead of all of them being either optional or not when using `optional_args`. 
Default values can also be set as you'd expect.

Examples:

```python
@bot.on_command('typedcommand')
def typed_command(str_arg, int_arg: int, float_arg: float):
    # user invokes "!typedcommand 123 123 123.0"
    # str_arg = '123', int_arg = 123, and float_arg = 123.0
    #
    # user invokes "!typedcommand a b c"
    # `InvalidCommandArgumentsError` is raised, and `on_invalid_arguments()` is called instead

from typing import Optional

@bot.on_command('optionalcommand')
def optional_command(required, optional: Optional[int] = 5):
    # user invoked "!optionalcommand abc 123"
    # required = 'abc', optional = 123
    #
    # user invoked "!optionalcommand abc
    # required = 'abc', optional = 5 (would be 0 if no default were set)
    #
    # user invoked "!optionalcommand
    # `InvalidCommandArgumentsError` is raised, and `on_invalid_arguments()` is called instead
```

The raw message received can also be retrieved by annotating the last argument with the
`Message` type. This message will be of type `Whisper` as defined in the 
[`dgg-chat`](https://github.com/gabrieljablonski/dgg-chat/blob/master/dgg_chat/messages/_messages.py#L100) package.
The available attributes are: 
 - `user`: Of type [`ChatUser`](https://github.com/gabrieljablonski/dgg-chat/blob/master/dgg_chat/messages/_messages.py#L6), contains the user's `nick` and their chat `features`.
 - `message_id`: Message id as defined in the chat backend, rarely useful.
 - `timestamp`: Unix timestamp for when the message was sent.
 - `content`: The raw message content the user originally sent.

Example:

```python
from dgg_chat_bot import Message

@bot.on_command('command')
def command(arg1, arg2, message: Message):
    print(message.user.nick)
```

**Obs.: If used, the `Message` argument HAS to be set as the last one.**

#### Command Description

One other very important aspect of implementing a command handler is the description.
The default `help` command implementation uses it to describe to the user what the
command does and how it's supposed to be used, so don't forget to write it!
To do so, use the standard way of documenting functions, the [docstrings](https://www.programiz.com/python-programming/docstrings).
Example:

```python
@bot.on_command('hello')
def say_hello(message: Message):
    """
    Replies hello to you!
    Example: "!hello".
    """
    bot.reply(f"Hi {message.user.nick}!")
```

Try to keep the description below 400 characters, since by default it is sent in one 
message along with other information, and messages have a size limit of 512 characters.

## Special Handlers

There are a few special scenarios worth mentioning:

 - The `help` command.
 - A command with invalid arguments was invoked.
 - An unknown command was invoked.
 - A message which didn't start with the command prefix ("!" by default) was received.
 - An unhandled exception was raised while processing the command.

All of them have default implementations ([which can be reviewed here](./dgg_chat_bot/_dgg_chat_bot.py#L56)), 
so implementing them is not necessary.

As [described before](#registering-commands), use the `override` option of the `on_command()` decorator to 
implement a custom `help` command. 

As for the other handlers, use the respective decorators: `on_invalid_arguments()`,
`on_unknown_command()`, `on_generic_message()`, and `on_fail()`.

Also, you can user the `before_every_command()` and `after_every_command()` to define handlers that
are called before and after every command. The expected signature for these functions
can be seen in the [`example.py`](./example.py#L133) file.

## Replying To Messages

As shown in the previous examples, the `reply()` function can be used to reply to the user who sent
the command being processed. There's also `reply_multine()`, which does what the name suggests.
Expect a small delay (~200-500 ms) between messages, since they'd get throttled otherwise.

Replying will be disabled by default. Follow down the source code to figure out how to enable it.
This is just to make sure you know what you're doing before allowing message sending.

## Authentication

Check the [authentication section](https://github.com/gabrieljablonski/dgg-chat#authentication) in the `dgg-chat` package description.

## Extra Features

This framework being built on top of the `dgg-chat` package, its functionality is exposed through the `chat`
attribute of the `DGGChatBot` class. So you can also use decorators to handle different events in chat,
like with `chat.on_chat_message()` and `chat.on_user_joined()`.

The `chat.send_whisper()` method is also available, which is specially useful when you need
to send a whisper not as an immediate reply (e.g.: a command that does something for a longer 
amount of time and sends a message when it is done).

For more details, go check out the [`dgg-chat` documentation](https://github.com/gabrieljablonski/dgg-chat).

## TODO

- Support regex for raising invalid args error automatically.
- Maybe use `multiprocessing` instead of `threading` for message sending?
- Improve the way **business logic** error messages are handled (maybe include message associated with it, if any?).
