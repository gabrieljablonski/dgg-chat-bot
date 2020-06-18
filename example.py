from os import getenv
from dotenv import load_dotenv
from dgg_chat.logging import setup_logger, DEBUG, INFO, WARNING
from dgg_chat_bot import DGGChatBot, Message


load_dotenv()
setup_logger(WARNING)

dgg_auth_token = getenv('DGG_AUTH_TOKEN')
bot = DGGChatBot(dgg_auth_token)


@bot.on_command('youreadumbfuck')
def youre_a_dumb_fuck(arg1, message: Message):
    print(arg1)
    print(message)
    bot.reply('YOURE A DUMB FUCK NOTMYTEMPO')


bot.run_forever()
