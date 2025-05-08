import telebot
import json
import schedule
import time
import threading
import os

## BOT INITIALISATION

class ExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        print(f"{time.ctime()}: error: {type(exception)}: {exception.args}")
        return True

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN, exception_handler=ExceptionHandler())

## SCHEDULER INIT

def add_weekly_points():
    amount = 20
    os.environ["MONEY"] = os.getenv["MONEY"] + amount
    users = {"azq878": 365279431, "catfish_nd": 801222813}
    
    for user_id in users.values():
        try:
            bot.send_message(user_id, f"сегодня пятница! добавлено {amount} денег.\nбаланс: {os.getenv("MONEY")}.")
        except Exception as e:
            print(f"ошибка при отправке сообщения пользователю {user_id}: {e}!!")


def run_scheduler():
    schedule.every().friday.at("08:00").do(add_weekly_points)
    while True:
        schedule.run_pending()
        time.sleep(60)

## BOT FUNCTIONS

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "привет, это бот для управления моими деньжаточками! \nсписок комманд: \n/balance - посмотреть баланс \n/add - добавить денег \n/spend - потратить деньги\n/audit - посмотреть логи транзакций")

@bot.message_handler(commands=['balance'])
def check_balance(message):
    if os.getenv["MONEY"] == 0:
        bot.send_message(message.chat.id, f"я бедный!!! у меня {os.getenv["MONEY"]} на балансе :(")
    elif os.getenv["MONEY"] > 0:
        bot.send_message(message.chat.id, f"у меня {os.getenv["MONEY"]} на балансе")

@bot.message_handler(commands=['spend'])
def spend_money(message):
    try:
        amount = int(message.text.split()[1])

        if os.getenv["MONEY"] >= amount:
            os.environ["MONEY"] = os.getenv["MONEY"] - amount
            bot.send_message(message.chat.id, f"списано {amount} денег. у меня осталось {os.getenv["MONEY"]}.")
        else:
            bot.send_message(message.chat.id, "недостаточно денег!")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "не забывай! для отнимания комманда: /spend 'деньга'.")

@bot.message_handler(commands=['add'])
def add_money(message):
    try:
        amount = int(message.text.split()[1])
        os.environ["MONEY"] = os.getenv["MONEY"] + amount
        bot.send_message(message.chat.id, f"начислено {amount} денег. не стоить злоупотреблять этой командой!")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, f"не забывай! для добавления денег комманда: /add 'деньга'. баланс: {os.getenv["MONEY"]}")

## MAIN
def main():
    threading.Thread(target=run_scheduler, daemon=True).start()
    print("Bot started.")
    bot.polling(non_stop=True, interval=5)

while True:
    try:
        main()
    except Exception as e:
        print(f"{time.ctime()}: error: {type(e)}: {e.args}")
        time.sleep(10)
