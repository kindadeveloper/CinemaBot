import telebot as tgb
from telebot import types
import requests
import json
import re

URLIMDB = "https://movie-database-imdb-alternative.p.rapidapi.com/"
URLIVA = "https://ivaee-internet-video-archive-entertainment-v1.p.rapidapi.com/entertainment/search/"
headersIMDB = {
    'x-rapidapi-host': "movie-database-imdb-alternative.p.rapidapi.com",
    'x-rapidapi-key': "33e34af31fmsh45e531bff2a7970p1f7d96jsn6a0c3e75f69d"
    }
headersIVA = {
        'x-rapidapi-host': "ivaee-internet-video-archive-entertainment-v1.p.rapidapi.com",
        'x-rapidapi-key': "33e34af31fmsh45e531bff2a7970p1f7d96jsn6a0c3e75f69d",
        'content-type': "application/json"
        }
responseBySearch = None
responseByID = None
userMessage = None
pageMarker = 1
bot = tgb.TeleBot('1107504191:AAFKdrsCNgf5rZLfIl0woHZVWD0VxYZ5FxU')

# счётчик запросов
def requestCount(fileName):
    readable = open(fileName)
    flag = len(readable.read())
    readable.close()
    if flag > 200:           # ограничение по количеству запросов
        exit()

    with open(fileName, "a+") as f:
        f.write("1")
        flag += 1
        f.close()
    if fileName == "requestsPerDay.txt":
        print("Requests per day: ", flag)
    else:
        print("Requests per month: ", flag)

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
    print(message)
    allTitles = responseBySearch["Search"]
    paginationKeys = types.InlineKeyboardMarkup(row_width=5)
    titlesList = f'Search results {(pageMarker-1)*10 + 1}-' \
        f'{(pageMarker-1)*10 + len(allTitles)} of {responseBySearch["totalResults"]}\n'
    keysRow1 = []
    keysRow2 = []
    navigationRow = []
    for title in allTitles:
        position = str(allTitles.index(title) + 1)
        keyNum = types.InlineKeyboardButton(text=position, callback_data=position)
        keysRow1.append(keyNum) if int(position) <= len(allTitles)/2 else keysRow2.append(keyNum)
        titlesList += f'\n{position}. {title["Title"]} ({title["Year"]})'
    if pageMarker != 1:
        navigationRow.append(types.InlineKeyboardButton(text="<=", callback_data="prevPage"))
    if pageMarker*10 <= int(responseBySearch["totalResults"]):
        navigationRow.append(types.InlineKeyboardButton(text="=>", callback_data="nextPage"))
    paginationKeys.add(*keysRow1, *keysRow2, *navigationRow)
    if not message.from_user.is_bot:
        bot.send_message(message.chat.id, titlesList, reply_markup=paginationKeys)
    else:
        bot.edit_message_text(text=titlesList, chat_id=message.chat.id, message_id=message.message_id, reply_markup=paginationKeys)

'''------------------------------------------------------------------------------------------------
Получение ТОП 250 фильмов по оценке зрителей с сайта. 
Запрос есть. Получаем список с ID каждого фильма (250). Метод get_top250()

top250_url = "http://www.imdb.com/chart/top"

def get_top250():
    r = requests.get(top250_url)
    html = r.text.split("\n")
    result = []
    for line in html:
        line = line.rstrip("\n")
        m = re.search(r'data-titleid="tt(\d+?)">', line)
        if m:
            _id = m.group(1)
            result.append(_id)
    return result

Получение названий этих фильмов по ID. Метод get_titles_top

def get_titles_top(titlesID:list):
    ia = imdb.IMDb()
    movies = []
    for index in range(len(titlesID)):
        movie = ia.get_movie(titlesID[index])
        print(f"id: {titlesID[index]}, movie: {movie['title']}")

'''
        
        
        
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

# выполнение и обработка запроса по жанру фильма
def makeRequestByGenre(message):
    requestCount("requestsPerMonth.txt")
    querystring = {"Genres": userMessage.text, "SortBy": "IvaRating", "ProgramTypes": "Movie"}
    response = requests.request("GET", URLIVA, headers=headersIVA, params=querystring)
    responseByGenre = json.loads(response.text)
    print(responseByGenre)

# выполнение и обработка запроса по ID фильма
def makeRequestByID(message, ID):
    requestCount("requestsPerDay.txt")
    global responseByID
    querystring = {"i": ID, "r": "json"}
    response = requests.request("GET", URLIMDB, headers=headersIMDB, params=querystring)
    responseByID = json.loads(response.text)
    print(responseByID)
    sendTitleByID(message)

# обработчик кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    global pageMarker
    if call.data == "searchByName":
        bot.send_message(call.message.chat.id, 'вводи название')
    elif call.data == "prevPage":
        pageMarker -= 1
        makeRequestByName(call.message)
    elif call.data == "nextPage":
        pageMarker += 1
        makeRequestByName(call.message)
    elif re.search('\d', call.data):
        makeRequestByID(call.message, responseBySearch["Search"][int(call.data) - 1]["imdbID"])

# выполнение и обработка запроса по названию фильма
def makeRequestByName(message):
    requestCount("requestsPerDay.txt")
    global responseBySearch
    querystring = {"page": str(pageMarker), "r": "json", "s": userMessage.text}
    response = requests.request("GET", URLIMDB, headers=headersIMDB, params=querystring)
    responseBySearch = json.loads(response.text)
    print(responseBySearch)
    pagination(message)

# обработчик текстового сообщения от юзера
@bot.message_handler(content_types=['text'])
def getMessageText(message):
    global userMessage
    userMessage = message
    # makeRequestByName(message)
    makeRequestByGenre(message)

# проверка на наличие новых сообщений у сервера телеги
bot.polling(none_stop=True, interval=0)
