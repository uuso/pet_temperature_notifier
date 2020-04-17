import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from secrets import bot_token, bot_access_secret, bot_access_ids, proxy_url
from drawyer import create_plotfile

dynamic_access_ids = dict(bot_access_ids)
REQUEST_KWARGS={
    'proxy_url': proxy_url,
}

updater = Updater(token=bot_token, request_kwargs=REQUEST_KWARGS, use_context=True)
dispatcher = updater.dispatcher

def start(update, context):
    if not update.effective_chat.id in dynamic_access_ids:
        print(f'Unauthorized: {update.effective_chat}')
        return
    send_file = create_plotfile(last_hours=8, suffix=update.effective_chat.id)
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(send_file, 'rb'))

def echo(update, context):
    if update.message.text == bot_access_secret:
        dynamic_access_ids[update.effective_chat.id] = update.effective_chat.username
        text = f'Successfully gained access to {update.effective_chat.id}: {update.effective_chat.username}'
        print(text)
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    # context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")





start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

echo_handler = MessageHandler(Filters.text, echo)
dispatcher.add_handler(echo_handler)

updater.start_polling()