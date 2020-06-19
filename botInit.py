import telebot as tgb
from telebot import types
import requests
import json
import re
from imdb import IMDb
import random

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
pagesData = {"Genre": {}, "Year": {}, "Director": {}, "Name": {}}
nextPageToken = None
userMessage = None
pageMarker = 1

top250_id = []
coming_soon_id = []

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

def pagination(message, resp, filterIdent):
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
        navigationRow.append(types.InlineKeyboardButton(text="<=", callback_data=f'prevPage@{filterIdent}'))
    if pageMarker*10 <= int(totalResults):
        navigationRow.append(types.InlineKeyboardButton(text="=>", callback_data=f'nextPage@{filterIdent}'))
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

def randomMovie(message):
    querystring = {"Minimum_IvaRating":random.randint(50, 100)}
    response = json.loads(requests.request("GET", URLIVA,
                                               headers=headersIVA,
                                               params=querystring).text)
    randomResp = random.choice(response["Hits"])["Source"]["Title"]
    IVAtoIMDB(message, randomResp)

def get_top250(url=TOP250_URL):
    '''
    Gives the top 250 movies from IMDb rate.
    Returns a dictionary with 2 key-value pairs:
    - 'Search' : list of 250 dictionaries each containing:
        - title of the movie;
        - year of release;
        - imdb ID.
    - 'totalResult' : number of found results (default=250)
    url is a url of the resource from which top is taken.
    By default, it's IMDb url.
    '''
    global top250_id
    r = requests.get(url)
    html = r.text.split("\n")
    for line in html:
        line = line.rstrip("\n")
        m = re.search(r'data-titleid="tt(\d+?)"', line)
        if m:
            _id = m.group(1)
            top250_id.append(_id)
    top250_id = list(set(top250_id))
    return top250_id


def get_coming_soon(url=COMING_SOON_URL):
    '''
    Gives the coming soon movies infrotmation.
    Returns a dictionary with 2 key-value pairs:
    - 'Search' : list of dictionaries each containing:
        - title of the movie;
        - year of release;
        - imdb ID.
    - 'totalResult' : number of found results.
    url is a url of the resource from which upcomings are taken.
    By default, it's IMDb url.
    '''
    global coming_soon_id
    # current date: 2020-06-01 in format 2020-06
    d = str(datetime.date.today())[:7]
    r = requests.get(url+d)
    html = r.text.split("\n")
    for line in html:
        line = line.rstrip("\n")
        m = re.search(r'<a href="/title/tt(\d+)/"', line)
        if m:
            _id = m.group(1)
            coming_soon_id.append(_id)
    coming_soon_id = list(set(coming_soon_id))

    return coming_soon_id

def getDict(movies_id: list, page=1):
    '''
    Add description.
    movies_id is a list of movie IDs from IMDb. IDs must be strings in format '010201'.
    page by default is 1, ignored if length of movies_id is less than 10.
    '''
    ia = IMDb()
    result_dict = {"Search": [], "totalResults": len(movies_id)}

    if len(movies_id) > 10:
        proper_ids = movies_id[(page-1)*10:(page*10)]
    else:
        proper_ids = movies_id

    for index in range(len(proper_ids)):
        movie = ia.get_movie(proper_ids[index])
        m_id = "tt{0}".format(proper_ids[index])
        title = movie['title']
        year = str(movie['year'])
        tmp = {"Title": title, "Year": year, "imdbID": m_id}
        result_dict["Search"].append(tmp)

    return result_dict

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

def checkResponse(message, response):
    if "Search" in response.keys() and response["Response"] == "False":
        bot.send_message(message.chat.id, "Sorry, nothing was found")
        return True
    elif "Hits" in response.keys() and len(response["Hits"]) == 0:
        bot.send_message(message.chat.id, "Sorry, nothing was found")
        return True
    else: return False

# выполнение и обработка запроса по фильтру
def makeRequestBy(message, token, filterIdent):
    querystring = {}
    response = None
    if filterIdent == "Genre":
        requestCount("requestsPerMonth.txt")
        querystring = {"Genres": userMessage.text.capitalize(),
                       "SortBy": "IvaRating",
                       "ProgramTypes": "Movie"}
        response = json.loads(requests.request("GET", URLIVA,
                                               headers=headersIVA,
                                               params=querystring).text)
    elif filterIdent == "Year":
        requestCount("requestsPerMonth.txt")
        querystring = {"YearRange_Start": userMessage.text,
                       "YearRange_End": userMessage.text,
                       "SortBy": "IvaRating",
                       "ProgramTypes": "Movie"}
        response = json.loads(requests.request("GET", URLIVA,
                                               headers=headersIVA,
                                               params=querystring).text)
    elif filterIdent == "Director":
        requestCount("requestsPerMonth.txt")
        dir_name = " ".join([name.capitalize() for name in userMessage.text.split(" ")])
        querystring = {"PersonNames": dir_name,
                       "Jobs": "Director",
                       "SortBy": "IvaRating",
                       "ProgramTypes": "Movie"}
        response = json.loads(requests.request("GET", URLIVA,
                                               headers=headersIVA,
                                               params=querystring).text)
    elif filterIdent == "Name":
        requestCount("requestsPerDay.txt")
        querystring = {"page": str(pageMarker), "r": "json", "s": userMessage.text}
        response = json.loads(requests.request("GET", URLIMDB,
                                               headers=headersIMDB,
                                               params=querystring).text)
    if len(pagesData[filterIdent][userMessage.text]) < pageMarker:
        if userMessage.text != "/start":
            if checkResponse(message, response): return 0
        if token: querystring.update({"NextPageToken": token})
        pagesData[filterIdent][userMessage.text].append(response)
        print(response)
        pagination(message, response, filterIdent)
    else:
        print(pagesData[filterIdent][userMessage.text][pageMarker - 1])
        pagination(message, pagesData[filterIdent][userMessage.text][pageMarker - 1], filterIdent)

# выполнение и обработка запроса по ID фильма
def makeRequestByID(message, ID):
    requestCount("requestsPerDay.txt")
    querystring = {"i": ID, "r": "json"}
    response = requests.request("GET", URLIMDB, headers=headersIMDB, params=querystring)
    responseByID = json.loads(response.text)
    print(responseByID)
    sendTitleByID(message, responseByID)

d = 0
@bot.message_handler(commands=['start'])
# метод ответа на команду
def startMessage(message):
    '''
    Greeting message, which pops up after entering /start.
    '''
    global d
    # init keyboard
    keyboard = types.InlineKeyboardMarkup()
    # кнопка поиска по названию
    randomMovieKey = types.InlineKeyboardButton(text="Random movie", callback_data="random")
    topKey = types.InlineKeyboardButton(text="Top 250 movies link", url=TOP250_URL)
    afishaKey = types.InlineKeyboardButton(text="Coming soon in cinema", url=COMING_SOON_URL)
    filterKey = types.InlineKeyboardButton(text="Filters", callback_data="filter")
    keyboard.add(filterKey, topKey, afishaKey, randomMovieKey)
    #EDIT
    questionText = "Choose an option"
    d = message
    bot.send_message(message.from_user.id, text=questionText, reply_markup=keyboard)

def filterMessage():
    '''
    EDIT
    Other message.
    '''
    # init keyboard
    keyboard = types.InlineKeyboardMarkup()
    # кнопка поиска по названию
    SearchByTitleKey = types.InlineKeyboardButton(text="Search by title", callback_data="SearchByTitle")
    SearchByGenreKey = types.InlineKeyboardButton(text="Search by genre", callback_data="SearchByGenre")
    SearchByYearKey = types.InlineKeyboardButton(text="Search by year", callback_data="SearchByYear")
    SearchByDirKey = types.InlineKeyboardButton(text="Search by director", callback_data="SearchByDir")
    keyboard.add(SearchByTitleKey, SearchByGenreKey, SearchByYearKey, SearchByDirKey)
    return keyboard

def checkMessage(message):
    global userMessage
    while userMessage == None:
        pass

# обработчик кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    global pageMarker
    global userMessage
    global d 
    delimiter = call.data.split('@')
    if delimiter[0] == "prevPage":
        pageMarker -= 1
        makeRequestBy(call.message, False, delimiter[1])
    elif delimiter[0] == "nextPage":
        pageMarker += 1
        makeRequestBy(call.message, nextPageToken, delimiter[1])
    elif re.search('\d', delimiter[0]):
        if nextPageToken:
            IVAtoIMDB(call.message, delimiter[1])
        else:
            makeRequestByID(call.message, delimiter[1])
    elif call.data == "random":
        randomMovie(call.message)
        #bot.send_message(call.message.chat.id, "Top 250")
    elif call.data == "filter":
        bot.send_message(call.message.chat.id, "Choose the filter", reply_markup=filterMessage())
    elif call.data == "SearchByTitle":
        checkMessage(call.message)
        print(type(userMessage))
        pagesData["Name"].update({f"{userMessage.text}": []})
        makeRequestBy(call.message, False, "Name")
    elif call.data == "SearchByGenre":
        checkMessage(call.message)
        pagesData["Genre"].update({f"{userMessage.text}": []})
        makeRequestBy(call.message, False, "Genre")
    elif call.data == "SearchByYear":
        checkMessage(call.message)
        pagesData["Year"].update({f"{userMessage.text}": []})
        makeRequestBy(call.message, False, "Year")
    elif call.data == "SearchByDir":
        checkMessage(call.message)
        pagesData["Director"].update({f"{userMessage.text}": []})
        makeRequestBy(call.message, False, "Director")


# обработчик текстового сообщения от юзера
@bot.message_handler(content_types=['text'])
def getMessageText(message):
    global userMessage
    userMessage = message
    # pagesData["Name"].update({f"{message.text}": []})
    # makeRequestBy(message, False, "Name")
    # pagesData["Genre"].update({f"{message.text}": []})
    # makeRequestBy(message, False, "Genre")
    # pagesData["Year"].update({f"{message.text}": []})
    # makeRequestBy(message, False, "Year")
    # pagesData["Director"].update({f"{message.text}": []})
    # makeRequestBy(message, False, "Director")

# проверка на наличие новых сообщений у сервера телеги
bot.polling(none_stop=True, interval=0)
