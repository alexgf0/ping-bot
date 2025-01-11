from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
import validators
import datetime
import requests

# keep track of active chat ids (need this to send warning notifications in ping_urls)
active_chats = set() 

# store the urls we want to ping
ping_pool = []
# dict to save (ping start time, last successful ping) 
ping_info = {}

async def ping_urls(context: ContextTypes.DEFAULT_TYPE):
  for url in ping_pool:
    res = requests.get(url)
    if res.status_code == 200:
      ping_info[url] = (ping_info[url][0], datetime.datetime.now())
    else:
      ping_info[url] = (ping_info[url][0], None)
      for chat_id in active_chats:
        await context.bot.send_message(chat_id=chat_id, text="ERROR for url:'{}' got response {}".format(url, res.status_code))

async def add_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
  active_chats.add(update.effective_chat.id)

  for url in context.args:
    if not validators.url(url):
      await update.message.reply_text("'{}' is not a valid url.\nAborting command.".format(url))
      return

  for url in context.args:
    ping_pool.append(url)
    ping_info[url] = (datetime.datetime.now(), None) # (start, last successful ping)

  await update.message.reply_text("Success.\nNew list: {}".format(ping_pool))


async def remove_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
  for url in context.args:
    if url in ping_pool:
      ping_pool.remove(url)
      ping_info.pop(url)
      await update.message.reply_text("Successfully removed url: '{}'".format(url))

    else:
      await update.message.reply_text("Url '{}' not found in list".format(url))

  await update.message.reply_text("New list: {}".format(ping_pool))

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if ping_info == {}:
    await update.message.reply_text("No urls to report for.\nTry the /help command and start adding some urls.")
    return

  report = "Report:"
  for key, value in ping_info.items():
    report += "\nurl:{}\n\t\tstarted tracking: {}\n\t\tlast successful ping: {}".format(key, value[0], value[1])
  
  
  await update.message.reply_text(report)


def main():
  token = "I'm not giving you my token"
  application = Application.builder().token(token).concurrent_updates(True).read_timeout(30).write_timeout(30).build()
  
  # run ping every 10 seconds
  application.job_queue.run_repeating(ping_urls, interval=10, first=1)
  
  # command handlers
  application.add_handler(CommandHandler("add_url", add_url))
  application.add_handler(CommandHandler("rm_url", remove_url))
  application.add_handler(CommandHandler("report", report))
  
  application.run_polling()


if __name__ == '__main__':
  main()

