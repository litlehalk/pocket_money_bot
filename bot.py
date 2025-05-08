import telebot
import json
import schedule
import time
import threading
import os

## BOT INITIALISATION

class ExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        log = load_log()
        log[time.ctime()] = f"error: {type(exception)}: {exception.args}"
        save_log(log)
        print(f"{time.ctime()}: error: {type(exception)}: {exception.args}")
        return True

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN, exception_handler=ExceptionHandler())

## FILE STORAGE INITIALISATION & FUNCTIONS

LOG_FILE = "/home/alloner/storage/log.json"
DATA_FILE = "/home/alloner/storage/data.json"
USERS_FILE = "/home/alloner/storage/users.json"
AUDIT_FILE = "/home/alloner/storage/audit.json"

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as f:
        json.dump({}, f)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"money": 0}, f)

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

if not os.path.exists(AUDIT_FILE):
    with open(AUDIT_FILE, "w") as f:
        json.dump({}, f)

def load_log():
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_log(log):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=4)

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"money": 0}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def load_audit():
    try:
        with open(AUDIT_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_audit(audit):
    with open(AUDIT_FILE, "w") as f:
        json.dump(audit, f, indent=4)

## WEEKLY SCHEDULER INITIALISATION

def add_weekly_points():
    amount = 20
    data = load_data()
    data["money"] += amount
    save_data(data)

    audit = load_audit()
    audit[time.ctime().replace('  ', ' ')] = f"weekly add,{amount},0000,bot"

    users = load_users()
    for user_id in users.values():
        try:
            bot.send_message(user_id, f"сегодня пятница! добавлено {amount} денег.\nбаланс: {data['money']}.")
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
    user_id = message.chat.id
    username = message.from_user.username
    users = load_users()

    if username not in users:
        users[username] = user_id
        save_users(users)

    bot.send_message(user_id, "привет, это бот для управления моими деньжаточками! \nсписок комманд: \n/balance - посмотреть баланс \n/add - добавить денег \n/spend - потратить деньги\n/audit - посмотреть логи транзакций")

@bot.message_handler(commands=['balance'])
def check_balance(message):
    data = load_data()

    if data['money'] == 0:
        bot.send_message(message.chat.id, f"я бедный!!! у меня {data['money']} на балансе :(")
    elif data['money'] > 0:
        bot.send_message(message.chat.id, f"у меня {data['money']} на балансе")

@bot.message_handler(commands=['spend'])
def spend_money(message):
    try:
        data = load_data()
        audit = load_audit()
        amount = int(message.text.split()[1])

        if data['money'] >= amount:
            data['money'] -= amount
            save_data(data)
            audit[time.ctime().replace('  ', ' ')] = f"spend,{amount},{message.chat.id},{message.from_user.username}"
            save_audit(audit)
            bot.send_message(message.chat.id, f"списано {amount} денег. у меня осталось {data['money']}.")
        else:
            bot.send_message(message.chat.id, "недостаточно денег!")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "не забывай! для отнимания комманда: /spend 'деньга'.")

@bot.message_handler(commands=['add'])
def add_money(message):
    try:
        data = load_data()
        audit = load_audit()
        amount = int(message.text.split()[1])
        data['money'] += amount
        save_data(data)
        audit[time.ctime().replace('  ', ' ')] = f"add,{amount},{message.chat.id},{message.from_user.username}"
        save_audit(audit)
        bot.send_message(message.chat.id, f"начислено {amount} денег. не стоить злоупотреблять этой командой!")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, f"не забывай! для добавления денег комманда: /add 'деньга'. баланс: {data['money']}")

@bot.message_handler(commands=['audit'])
def audit(message):
    try:
        audit = load_audit()
        audit_string = ''
        for timestamp in audit:
            line_data = audit[timestamp].split(',')
            audit_string += f"{line_data[3]} {line_data[0]} {line_data[1]} at {timestamp}\n"
        bot.send_message(message.chat.id, audit_string)
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, f"чёт пошло не так, посмотри логи")


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
