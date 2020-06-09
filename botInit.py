import telebot as tgb
from telebot import types
import requests
import json
import re

URL = "https://movie-database-imdb-alternative.p.rapidapi.com/"
headers = {
    'x-rapidapi-host': "movie-database-imdb-alternative.p.rapidapi.com",
    'x-rapidapi-key': "33e34af31fmsh45e531bff2a7970p1f7d96jsn6a0c3e75f69d"
    }
responseBySearch = None
responseByID = None
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

def pagination(message):
    allTitles = responseBySearch["Search"]
    paginationKeys = types.InlineKeyboardMarkup()
    titlesList = ''
    keysPart1 = []
    keysPart2 = []
    for title in allTitles:
        position = str(allTitles.index(title) + 1)
        keyNum = types.InlineKeyboardButton(text=position, callback_data=position)
        keysPart1.append(keyNum) if int(position) <= 5 else keysPart2.append(keyNum)
        titlesList += f'\n{position}. {title["Title"]} ({title["Year"]})'
    keyPrev = types.InlineKeyboardButton(text="<=", callback_data="prevPage")
    keyNext = types.InlineKeyboardButton(text="=>", callback_data="nextPage")
    paginationKeys.add(*keysPart1)
    paginationKeys.add(*keysPart2)
    paginationKeys.add(keyPrev, keyNext)
    bot.send_message(message.chat.id, titlesList, reply_markup=paginationKeys)

# отправка постера с описанием
def sendTitleByID(message):
    posterCaption = f'{responseByID["Title"]} ({responseByID["Year"]})\n' \
        f'\nRated: {responseByID["Rated"]}' \
        f'\nReleased: {responseByID["Released"]}' \
        f'\nRuntime: {responseByID["Runtime"]}' \
        f'\nAction: {responseByID["Genre"]}' \
        f'\nCast: {responseByID["Actors"]}\n' \
        f'\n{responseByID["Plot"]}'
    bot.send_photo(message.chat.id, responseByID["Poster"], posterCaption)

# выполнение и обработка запроса по ID фильма
def makeRequestByID(message, ID):
    requestCount()
    global responseByID
    querystring = {"i": ID, "r": "json"}
    response = requests.request("GET", URL, headers=headers, params=querystring)
    responseByID = json.loads(response.text)
    print(responseByID)
    sendTitleByID(message)

# обработчик кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if call.data == "searchByName":
        bot.send_message(call.message.chat.id, 'вводи название')
    elif call.data == "prevPage":
        bot.send_message(call.message.chat.id, "sup 2ch")
    elif call.data == "nextPage":
        bot.send_message(call.message.chat.id, text="bye 2ch")
    elif re.search('\d', call.data):
        makeRequestByID(call.message, responseBySearch["Search"][int(call.data) - 1]["imdbID"])

# выполнение и обработка запроса по названию фильма
def makeRequestByName(message):
    requestCount()
    global responseBySearch
    querystring = {"page": "1", "r": "json", "s": message.text}
    response = requests.request("GET", URL, headers=headers, params=querystring)
    responseBySearch = json.loads(response.text)
    print(responseBySearch)
    pagination(message)

# обработчик текстового сообщения от юзера
@bot.message_handler(content_types=['text'])
def getMessageText(message):
    makeRequestByName(message)

# проверка на наличие новых сообщений у сервера телеги
bot.polling(none_stop=True, interval=0)
