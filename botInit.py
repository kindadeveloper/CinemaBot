import telebot as tgb
from telebot import types
import requests
import json
import re
import imdb

URLIMDB = "https://movie-database-imdb-alternative.p.rapidapi.com/"
URLIVA = "https://ivaee-internet-video-archive-entertainment-v1.p.rapidapi.com/entertainment/search/"

TOP250_URL = "http://www.imdb.com/chart/top"
COMING_SOON_URL = "https://www.imdb.com/movies-coming-soon/"

headersIMDB = {
    'x-rapidapi-host': "movie-database-imdb-alternative.p.rapidapi.com",
    'x-rapidapi-key': "33e34af31fmsh45e531bff2a7970p1f7d96jsn6a0c3e75f69d"
    }
headersIVA = {
        'x-rapidapi-host': "ivaee-internet-video-archive-entertainment-v1.p.rapidapi.com",
        'x-rapidapi-key': "33e34af31fmsh45e531bff2a7970p1f7d96jsn6a0c3e75f69d",
        'content-type': "application/json"
        }
pagesData = {}
nextPageToken = None
userMessage = None
pageMarker = 1
bot = tgb.TeleBot('1107504191:AAFKdrsCNgf5rZLfIl0woHZVWD0VxYZ5FxU')


def requestCount(fileName):
    '''
    Counts requests made per day or per month. Maximum value is 200 requests per day.
    
    fileName is either a text or byte string giving the name (and the path if the file isn't in the current working directory) of the file to be opened.
    '''
    readable = open(fileName)
    flag = len(readable.read())
    readable.close()
    if flag > 200:          
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
    '''
    Greeting message, which pops up after entering /start.
    '''
    # init keyboard
    keyboard = types.InlineKeyboardMarkup()
    # кнопка поиска по названию
    searchByNameKey = types.InlineKeyboardButton(text="Найти фильм по названию", callback_data="searchByName")
    keyboard.add(searchByNameKey)
    questionText = "чо хош?"
    bot.send_message(message.from_user.id, text=questionText, reply_markup=keyboard)

def pagination(message, resp):
    global nextPageToken
    normAPI = None
    allTitles = None
    totalResults = None
    if "Search" in resp.keys():
        normAPI = True
        allTitles = resp["Search"]
        totalResults = resp["totalResults"]
    if "Hits" in resp.keys():
        normAPI = False
        allTitles = resp["Hits"]
        totalResults = resp["Total"]
        nextPageToken = resp["NextPageToken"]
    paginationKeys = types.InlineKeyboardMarkup(row_width=5)
    titlesList = f'Search results {(pageMarker-1)*10 + 1}-' \
        f'{(pageMarker-1)*10 + len(allTitles)} of {totalResults}\n'
    keysRow1 = []
    keysRow2 = []
    navigationRow = []
    for title in allTitles:
        position = str(allTitles.index(title) + 1)
        if normAPI:
            callbackData = f'{position}@{resp["Search"][int(position) - 1]["imdbID"]}'
        else:
            callbackData = f'{position}@{title["Source"]["Title"]}'
        keyNum = types.InlineKeyboardButton(text=position, callback_data=callbackData)
        keysRow1.append(keyNum) if int(position) <= len(allTitles)/2 else keysRow2.append(keyNum)
        if normAPI:
            titlesList += f'\n{position}. {title["Title"]} ({title["Year"]})'
        else:
            titlesList += f'\n{position}. {title["Source"]["Title"]} ({title["Source"]["Year"]})'
    if pageMarker != 1:
        navigationRow.append(types.InlineKeyboardButton(text="<=", callback_data=f'prevPage'))
    if pageMarker*10 <= int(totalResults):
        navigationRow.append(types.InlineKeyboardButton(text="=>", callback_data=f'nextPage'))
    paginationKeys.add(*keysRow1, *keysRow2, *navigationRow)
    if not message.from_user.is_bot:
        bot.send_message(message.chat.id, titlesList, reply_markup=paginationKeys)
    else:
        bot.edit_message_text(text=titlesList, chat_id=message.chat.id, message_id=message.message_id, reply_markup=paginationKeys)

def IVAtoIMDB(message, title):
    querystring = {"page": 1, "r": "json", "s": title}
    response = json.loads(requests.request("GET", URLIMDB, headers=headersIMDB, params=querystring).text)
    requestCount("requestsPerDay.txt")
    makeRequestByID(message, response["Search"][0]["imdbID"])

# обработчик кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    global pageMarker
    if call.data == "searchByName":
        bot.send_message(call.message.chat.id, 'вводи название')
    elif call.data == "prevPage":
        pageMarker -= 1
        if nextPageToken == None:
            makeRequestByName(call.message)
        else:
            # makeRequestByGenre(call.message, False)
            # makeRequestByYear(call.message, False)
            makeRequestByDirector(call.message, False)
    elif call.data == "nextPage":
        pageMarker += 1
        if nextPageToken == None:
            makeRequestByName(call.message)
        else:
            # makeRequestByGenre(call.message, nextPageToken)
            # makeRequestByYear(call.message, nextPageToken)
            makeRequestByDirector(call.message, nextPageToken)
    elif re.search('\d', call.data.split('@')[0]):
        if nextPageToken:
            IVAtoIMDB(call.message, call.data.split('@')[1])
        else:
            makeRequestByID(call.message, call.data.split('@')[1])

def get_top250():
    '''
    Gives the top 250 movies from IMDb rate.
    Returns a dictionary with 2 key-value pairs:
    - 'Search' : list of 250 dictionaries each containing:
        - title of the movie;
        - year of release;
        - imdb ID.
    - 'totalResult' : number of found results (default=250)
    '''
    r = requests.get(TOP250_URL)
    html = r.text.split("\n")
    movies_id = []
    for line in html:
        line = line.rstrip("\n")
        m = re.search(r'data-titleid="tt(\d+?)">', line)
        if m:
            _id = m.group(1)
            movies_id.append(_id)

    ia = imdb.IMDb()
    movies = []
    responseTop = {"Search":[], "totalResults":len(movies_id)}
    
    for index in range(len(movies_id)):
        movie = ia.get_movie(movies_id[index])
        m_id = movies_id[index]
        title = movie['title']
        year = str(movie['year'])
        tmp = {"Title":title, "Year":year, "imdbID":m_id}
        responseTop.add(tmp)
    
    return responseTop

        
def get_coming_soon():
    '''
    Gives the coming soon movies infrotmation.
    Returns a dictionary with 2 key-value pairs:
    - 'Search' : list of dictionaries each containing:
        - title of the movie;
        - year of release;
        - imdb ID.
    - 'totalResult' : number of found results.
    '''
    d = str(datetime.date.today())[:7]
    r = requests.get(COMING_SOON_URL+d)
    html = r.text.split("\n")
    movies_id = []
    ms = []
    for line in html:
        line = line.rstrip("\n")
        m = re.search(r'<a href="/title/tt(\d+)/"', line)
        ms.append(m)
        if m:
            _id = m.group(1)
            movies_id.append(_id)
    movies_id = list(set(movies_id))
    ia = imdb.IMDb()
    responseComingSoon = {"Search":[], "totalResults":len(movies_id)}
    
    for index in range(len(movies_id)):
        movie = ia.get_movie(movies_id[index])
        m_id = movies_id[index]
        title = movie['title']
        year = str(movie['year'])
        tmp = {"Title":title, "Year":year, "imdbID":m_id}
        responseComingSoon.add(tmp)
    
    return responseComingSoon   
        

# отправка постера с описанием
def sendTitleByID(message, respID):
    posterCaption = f'{respID["Title"]} ({respID["Year"]})\n' \
        f'\nRated: {respID["Rated"]}' \
        f'\nReleased: {respID["Released"]}' \
        f'\nRuntime: {respID["Runtime"]}' \
        f'\nAction: {respID["Genre"]}' \
        f'\nCast: {respID["Actors"]}\n' \
        f'\n{respID["Plot"]}'
    bot.send_photo(message.chat.id, respID["Poster"], posterCaption)

# выполнение и обработка запроса по режиссёру фильма
def makeRequestByDirector(message, token):
    if len(pagesData["Director"]) < pageMarker:
        requestCount("requestsPerMonth.txt")
        querystring = {"PersonNames": "James Cameron", "Jobs": "Director", "SortBy": "IvaRating", "ProgramTypes": "Movie"}
        if token: querystring.update({"NextPageToken": token})
        response = requests.request("GET", URLIVA, headers=headersIVA, params=querystring)
        responseByDirector = json.loads(response.text)
        pagesData["Director"].append(responseByDirector)
        print(responseByDirector)
        pagination(message, responseByDirector)
    else:
        print(pagesData["Director"][pageMarker - 1])
        pagination(message, pagesData["Director"][pageMarker - 1])

# выполнение и обработка запроса по году фильма
def makeRequestByYear(message, token):
    if len(pagesData["Year"]) < pageMarker:
        requestCount("requestsPerMonth.txt")
        querystring = {"YearRange_Start": userMessage.text, "YearRange_End": userMessage.text, "SortBy": "IvaRating", "ProgramTypes": "Movie"}
        if token: querystring.update({"NextPageToken": token})
        response = requests.request("GET", URLIVA, headers=headersIVA, params=querystring)
        responseByYear = json.loads(response.text)
        pagesData["Year"].append(responseByYear)
        print(responseByYear)
        pagination(message, responseByYear)
    else:
        print(pagesData["Year"][pageMarker - 1])
        pagination(message, pagesData["Year"][pageMarker - 1])

# выполнение и обработка запроса по жанру фильма
def makeRequestByGenre(message, token):
    if len(pagesData["Genre"]) < pageMarker:
        requestCount("requestsPerMonth.txt")
        querystring = {"Genres": userMessage.text, "SortBy": "IvaRating", "ProgramTypes": "Movie"}
        if token: querystring.update({"NextPageToken": token})
        response = requests.request("GET", URLIVA, headers=headersIVA, params=querystring)
        responseByGenre = json.loads(response.text)
        pagesData["Genre"].append(responseByGenre)
        print(responseByGenre)
        pagination(message, responseByGenre)
    else:
        print(pagesData["Genre"][pageMarker - 1])
        pagination(message, pagesData["Genre"][pageMarker - 1])

# выполнение и обработка запроса по ID фильма
def makeRequestByID(message, ID):
    requestCount("requestsPerDay.txt")
    querystring = {"i": ID, "r": "json"}
    response = requests.request("GET", URLIMDB, headers=headersIMDB, params=querystring)
    responseByID = json.loads(response.text)
    print(responseByID)
    sendTitleByID(message, responseByID)

# выполнение и обработка запроса по названию фильма
def makeRequestByName(message):
    requestCount("requestsPerDay.txt")
    querystring = {"page": str(pageMarker), "r": "json", "s": userMessage.text}
    response = requests.request("GET", URLIMDB, headers=headersIMDB, params=querystring)
    responseByName = json.loads(response.text)
    print(responseByName)
    pagination(message, responseByName)

# обработчик текстового сообщения от юзера
@bot.message_handler(content_types=['text'])
def getMessageText(message):
    global userMessage
    userMessage = message
    makeRequestByName(message)
    # pagesData.update({"Genre": []})
    # makeRequestByGenre(message, False)
    # pagesData.update({"Year": []})
    # makeRequestByYear(message, False)
    # pagesData.update({"Director": []})
    # makeRequestByDirector(message, False)

# проверка на наличие новых сообщений у сервера телеги
bot.polling(none_stop=True, interval=0)
