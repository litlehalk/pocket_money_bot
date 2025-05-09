import telebot
import json
import schedule
import time
import threading
import os
import psycopg2
from datetime import datetime
from psycopg2.extras import RealDictCursor

## BOT INITIALISATION

class ExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        print(f"{time.ctime()}: error: {type(exception)}: {exception.args}")
        return True

DATABASE_URL = os.getenv("DATABASE_URL")
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN, exception_handler=ExceptionHandler())

## SCHEDULER INIT

def add_weekly_points():
    amount = 20
    new_total = get_last_total() + amount
    save_value(amount, 'BOT', new_total)
    
    users = {"azq878": 365279431, "catfish_nd": 801222813}
    for user_id in users.values():
        try:
            bot.send_message(user_id, f"сегодня пятница! добавлено {amount} денег.\nбаланс: {new_total}.")
        except Exception as e:
            print(f"ошибка при отправке сообщения пользователю {user_id}: {e}!!")


def run_scheduler():
    schedule.every().friday.at("08:16").do(add_weekly_points)
    while True:
        schedule.run_pending()
        time.sleep(60)

## BOT FUNCTIONS

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "привет, это бот для управления моими деньжаточками! \nсписок комманд: \n/balance - посмотреть баланс \n/add - добавить денег \n/spend - потратить деньги\n/audit - посмотреть логи транзакций")

@bot.message_handler(commands=['balance'])
def check_balance(message):
    last_total = get_last_total()
    if last_total == 0:
        bot.send_message(message.chat.id, f"я бедный!!! у меня {last_total} на балансе :(")
    elif last_total > 0:
        bot.send_message(message.chat.id, f"у меня {last_total} на балансе")

@bot.message_handler(commands=['spend'])
def spend_money(message):
    try:
        amount = int(message.text.split()[1])
        last_total = get_last_total()
        
        if last_total >= amount:
            new_total = last_total - amount
            save_value(-amount, str(message.chat.id), new_total)
            bot.send_message(message.chat.id, f"списано {amount} денег. у меня осталось {new_total}.")
        else:
            bot.send_message(message.chat.id, "недостаточно денег!")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "не забывай! для отнимания комманда: /spend 'деньга'.")

@bot.message_handler(commands=['add'])
def add_money(message):
    try:
        amount = int(message.text.split()[1])
        last_total = get_last_total()
        new_total = last_total + amount
        save_value(amount, str(message.chat.id), new_total)
        bot.send_message(message.chat.id, f"начислено {amount} денег. Не стоит злоупотреблять этой командой! На счету {new_total}.")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, f"не забывай! для добавления денег комманда: /add 'деньга'.")

def save_value(amount: int, user: str, total: int):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        insert_query = """
            INSERT INTO pocket_money (amount, user, total, date)
            VALUES (%s, %s, %s, %s)
        """
        cur.execute(insert_query, (amount, user, total, datetime.utcnow()))
        
        conn.commit()
        cur.close()
        conn.close()
        print("Value saved successfully.")
    except Exception as e:
        print(f"Error saving value: {e}")

def get_last_total() -> int:
    entries = get_last_entries(1)
    for entry in entries:
        if entry.get("total") is not None:
            return entry["total"]
    return 0

def get_last_entries(n):
    try:
        connection = psycopg2.connect(DATABASE_URL)
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM pocket_money ORDER BY date DESC LIMIT %s;",
                (n,)
            )
            entries = cursor.fetchall()
            return entries if entries else []
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if connection:
            connection.close()

def iniDB():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS pocket_money (id SERIAL PRIMARY KEY, amount INTEGER, user TEXT, total INTEGER, date TIMESTAMP);")
    conn.commit()

## MAIN
def main():
    iniDB()
    threading.Thread(target=run_scheduler, daemon=True).start()
    print("Bot started.")
    bot.polling(non_stop=True, interval=5)

main()
