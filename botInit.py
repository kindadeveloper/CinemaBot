import telebot as tgb
from telebot import types
import requests
import json

URL = "https://movie-database-imdb-alternative.p.rapidapi.com/"
headers = {
    'x-rapidapi-host': "movie-database-imdb-alternative.p.rapidapi.com",
    'x-rapidapi-key': "33e34af31fmsh45e531bff2a7970p1f7d96jsn6a0c3e75f69d"
    }
parsedRequest = None
bot = tgb.TeleBot('1107504191:AAFKdrsCNgf5rZLfIl0woHZVWD0VxYZ5FxU')

# счётчик запросов
def requestCount():
    readable = open("REQUEST_COUNTER.txt")
    flag = len(readable.read())
    readable.close()
    if flag > 100:           # ограничение по количеству запросов
        exit()

    with open("REQUEST_COUNTER.txt", "a+") as f:
        f.write("1")
        flag += 1
        f.close()
    print("Requests number: ", flag)

@bot.message_handler(commands=['start'])
# метод ответа на команду
def startMessage(message):
    # init keyboard
    keyboard = types.InlineKeyboardMarkup()
    # кнопка поиска по названию
    searchByNameKey = types.InlineKeyboardButton(text="Найти фильм по названию", callback_data="searchByName")
    keyboard.add(searchByNameKey)
    questionText = "чо хош?"
    bot.send_message(message.from_user.id, text=questionText, reply_markup=keyboard)

# обработчик кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if call.data == "searchByName":
        bot.send_message(call.message.chat.id, 'вводи название')

# выполнение и обработка запроса
def makeRequest(title):
    requestCount()
    querystring = {"page": "1", "r": "json", "s": title.text}
    response = requests.request("GET", URL, headers=headers, params=querystring)
    parsedRequest = json.loads(response.text)
    print(parsedRequest)
    firstResponse = parsedRequest["Search"][0]
    bot.send_photo(title.from_user.id, firstResponse["Poster"], firstResponse["Title"])

# обработчик текстового сообщения от юзера
@bot.message_handler(content_types=['text'])
def getMessageText(message):
    makeRequest(message)

# проверка на наличие новых сообщений у сервера телеги
bot.polling(none_stop=True, interval=0)
