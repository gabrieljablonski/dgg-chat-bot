from os import getenv
from re import findall
from random import randint
from typing import Optional, Union
from itertools import islice
from dotenv import load_dotenv

from dgg_chat.logging import setup_logger, DEBUG, INFO, WARNING
from dgg_chat.messages import UserJoined, UserQuit, ServedConnections
from dgg_chat.overrustle_logs import DGGLogs
from dgg_chat_bot import DGGChatBot, Message
from dgg_chat_bot.exceptions import InvalidCommandArgumentsError


load_dotenv()
setup_logger(INFO)

dgg_auth_token = getenv('DGG_AUTH_TOKEN')
extra_help = 'More details at github.com/gabrieljablonski/dgg-chat-bot.'
bot = DGGChatBot(dgg_auth_token, extra_help=extra_help)


users_stalked = {}
reminders = {}


@bot.on_command('logs')
def logs(user, amount: Optional[int] = 5, message: Message = None):
    """
    "!logs <user> <amount>".
    Gets the last <amount> messages sent by <user> (up to 10).
    <user> defaults to sender.
    <amount> default to 5.
    """

    user = user or message.user.nick
    msg = f"Retrieving last {amount} messages sent by {user}..."
    bot.reply(msg)

    # this is not an efficient way to do this btw, caching could help
    last_n = [m.original for m in tuple(DGGLogs.get_user_logs(user))[-amount:]]
    bot.reply_multiline(last_n)


@bot.on_command('stalk')
def stalk(stalked, message: Message):
    """
    "!stalk <user>".
    Receive a message whenever <user> joins or leaves the chat.
    Use "!unstalk <user>" to stop.
    """

    users_stalked.setdefault(stalked.lower(), set()).add(message.user.nick)
    bot.reply(f"All set! Next time {stalked} joins or leaves the chat I'll let you know.")


@bot.on_command('unstalk')
def unstalk(stalked, message: Message):
    """
    "!unstalk <user>".
    Stop receiving a message whenever <user> joins or leaves the chat.
    """

    try:
        users_stalked.get(stalked.lower(), set()).remove(message.user.nick)
    except KeyError:
        msg = f"It doesn't seem you're stalking {stalked} 🤔."
    else:
        msg = f"All set! You're no longer stalking {stalked}."

    bot.reply(msg)


@bot.on_command('remindme', 'remind')
def remindme(note, message: Message):
    """
    "!remindme <note>".
    Reminds you message <note> next time you connect to chat.
    <note> should not exceed 400 characters.
    """

    if len(note) > 400:
        return bot.reply('Sorry, that note is too large. Try something smaller than 400 characters.')

    reminders[message.user.nick] = note or 'no message set'
    bot.reply("All set! Next time you connect to chat I'll remind you of that.")


@bot.on_command('roll')
def roll(expr):
    """
    "!roll <expression>".
    Rolls dice. 
    The expression format is as follows: "<N>d<P>+<B>",
    in which <N> is the amount of dice to roll, <P> is the die size, 
    and <B> is the base amount to add (or subtract)
    (if you know regular expressions: "(\\d+)d(\\d+)([+-]\\d+)?").
    <N> cannot be higher than 20, and <B> is optional.
    Examples: "!roll 3d6", "!roll 5d10+5", "!roll 3d12-2".
    """
    match = findall(r'(\d+)d(\d+)([+-]\d+)?', expr)
    if not match:
        raise InvalidCommandArgumentsError(expr)
    
    n, p, b = match[0]
    try:
        n, p, b = int(n), int(p), int(b or 0)
        if 0 > n > 20 or p <= 0:
            raise ValueError
    except ValueError:
        raise InvalidCommandArgumentsError(expr)

    rolls = [
        randint(1, p)
        for _ in range(n)
    ]

    sign = '-' if b < 0 else '+'
    base = f" {sign} {abs(b)}*" if b else ''

    if n == 1 and not b:
        msg = f"Rolled: {rolls[0]}"
    else:
        msg = f"Rolled: {' + '.join(str(r) for r in rolls)}{base} = {sum(rolls) + b}"
    bot.reply(msg)


@bot.chat.on_user_joined
def reminder(message: UserJoined):
    user = message.user.nick
    if user in reminders:
        msg = f"Hi {user}! Last time you were here you asked me to remind you of this: {reminders[user]}"
        bot.chat.send_whisper(user, msg)
        del reminders[user]


@bot.chat.on_user_quit
@bot.chat.on_user_joined
def stalking(message: Union[UserJoined, UserQuit]):
    user = message.user.nick
    if (u := user.lower()) in users_stalked:
        event = 'joined' if type(message) is UserJoined else 'left'
        msg = f"{user} just {event} the chat."
        for stalker in users_stalked[u]:
            # be mindful with implementations like these,
            # since you'll likely get throttled
            bot.chat.send_whisper(stalker, msg)


bot.run_forever()
