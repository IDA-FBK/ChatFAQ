import os 
import time
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CallbackContext, CommandHandler
from openai import OpenAI
from dotenv import load_dotenv
from retrieval import *
import asyncio

global history
history = {}

pairs = {}
usage = {}

#information for set up 
load_dotenv() 
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
client = OpenAI(api_key = os.getenv("API_KEY_OPENAI"))

#if the assistant is not present in your dashboard, it has to be created, otherwise retrieved
def retrieve_or_create_assistant(search_name):
    list_assistants = client.beta.assistants.list(
        order="desc",
        limit="20",
    )
    id_ass = ''
    for assistant in list_assistants.data:
        if assistant.name == search_name:
            id_ass = assistant.id
            break

    if id_ass != '':
        assistant = client.beta.assistants.retrieve(id_ass)
    else:
        assistant = client.beta.assistants.create(
            instructions = "Sei un medico ginecologo, devi rispondere alle domande di una donna incinta",
            name = search_name,
            tools=[{"type": "code_interpreter"}],
            model = "gpt-4o-2024-05-13",
            temperature = 0.2,
        )
    return assistant


assistant = retrieve_or_create_assistant('Doctor Doctor')

def control_words (ai_response, user_id, user_message): #be sure to have a response around eighty/ninety words
    text = ai_response.split(' ')
    count = 0
    while len(text) > 105:
        count = count + 1
        print('lunghezza sbagliata: ', len(text))
        user_message = 'La risposta che mi hai dato non è corretta in quanto non è circa di ottanta parole: "' + ai_response + ' ". Ti ripeto la domanda: ' + user_message
        ai_response = send_msg_to_assistant(user_message, user_id)
        text = ai_response.split(' ')
        if count == 2:
            print('sto elaborando una risposta')
    return ai_response, count

def send_msg_to_assistant(query, user_id):
    id = pairs[user_id]

    message = client.beta.threads.messages.create(
        thread_id=id,
        role="user",
        content=query
    )

    run = client.beta.threads.runs.create(
        thread_id=id,
        assistant_id=assistant.id
    )

    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=id,
            run_id=run.id,
        )
        time.sleep(0.5)

    run_mex = client.beta.threads.runs.retrieve(
        thread_id=id,
        run_id=run.id
    )

    messages = client.beta.threads.messages.list(
        thread_id=run_mex.thread_id
    )

    response = messages.data[0].content[0].text.value

    return response

async def reply_to_user(update: Update, context: CallbackContext) -> None:

    chat_id = update.message.chat_id

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await asyncio.sleep(2) 
    
    user_id = update.message.from_user.id
    if user_id not in usage:
        thread = client.beta.threads.create()
        pairs[user_id] = thread.id
        usage[user_id] = chat_id 
    user_msg = update.message.text + '\nDammi la risposta senza ripetere la domanda in circa ottanta parole.'

    docs, scores = ret_docs(user_msg)
    

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await asyncio.sleep(2)

    ai_response = send_msg_to_assistant(user_msg, user_id)
    response, count = control_words(ai_response, user_id, user_msg)

    msg = response + '\n\n' + 'Per maggiori informazioni consultare: \n\t' if len(docs)>0 else response

    for x in range(len(docs)):
        msg = msg + docs[x] + '\n\t'
    
    await update.message.reply_text(msg)



async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await asyncio.sleep(2)
    await update.message.reply_text('Ciao! Come posso aiutarti?')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await asyncio.sleep(2)
    await update.message.reply_text(
        'Ciao! Questi sono i comandi che puoi utilizzare: '
        '\n \t /start - puoi assicurati di avere una risposta dal chatbot e iniziare la conversazione (ma non cancella quelle prima)'
        '\n \t /help - lista dei comandi che puoi utilizzare'
    )

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    bot = Bot(TOKEN)

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))

    app.add_handler(MessageHandler(filters.TEXT & (~ filters.COMMAND), reply_to_user))

    app.add_error_handler(error)

    print('Polling...')

    app.run_polling(poll_interval=3) 