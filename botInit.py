import requests
import json
import re
import random

import config

from telebot import types, TeleBot

pagesData = {"Genre": {}, "Year": {}, "Director": {}, "Name": {}}
nextPageToken = None
userMessage = None
pageMarker = 1

bot = TeleBot(config.token)


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
    '''
    Processes data to show in bot. Maximum value is 10 units per message.

    message is a system message from the current session in chat;
    resp is a dictionary with short information about the film;
    filterIdent is a string parameter for separation searching by filters;
    '''
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
        keyNum = types.InlineKeyboardButton(
            text=position, callback_data=callbackData)
        keysRow1.append(keyNum) if int(position) <= len(
            allTitles)/2 else keysRow2.append(keyNum)
        if normAPI:
            titlesList += f'\n{position}. {title["Title"]} ({title["Year"]})'
        else:
            titlesList += f'\n{position}. {title["Source"]["Title"]} ({title["Source"]["Year"]})'
    if pageMarker != 1:
        navigationRow.append(types.InlineKeyboardButton(text="<=",
                                                        callback_data=f'prevPage@{filterIdent}'))
    if pageMarker*10 <= int(totalResults):
        navigationRow.append(types.InlineKeyboardButton(
            text="=>", callback_data=f'nextPage@{filterIdent}'))
    paginationKeys.add(*keysRow1, *keysRow2, *navigationRow)
    if not message.from_user.is_bot:
        bot.send_message(message.chat.id, titlesList,
                         reply_markup=paginationKeys)
    else:
        bot.edit_message_text(text=titlesList, chat_id=message.chat.id,
                              message_id=message.message_id,
                              reply_markup=paginationKeys)


def IVAtoIMDB(message, title):
    querystring = {"page": 1, "r": "json", "s": title}
    response = json.loads(requests.request("GET", config.URLIMDB,
                                           headers=config.headersIMDB,
                                           params=querystring).text)
    requestCount("requestsPerDay.txt")
    makeRequestByID(message, response["Search"][0]["imdbID"])


def randomMovie(message):
    '''
    Returns a random movies.

    message is a system message from the bot.
    '''
    querystring = {"Minimum_IvaRating": random.randint(50, 100)}
    response = json.loads(requests.request("GET", config.URLIVA,
                                           headers=config.headersIVA,
                                           params=querystring).text)
    randomResp = random.choice(response["Hits"])["Source"]["Title"]
    IVAtoIMDB(message, randomResp)


def sendTitleByID(message, respID):
    '''
    Returns a poster with short information about the film.

    message is a system message from the bot;
    respID is a dictionary with information about the film, including:
    - title;
    - rating;
    - release date;
    - runtime;
    - genres;
    - cast;
    - short plot description;
    - link to the poster.
    '''
    posterCaption = f'{respID["Title"]} ({respID["Year"]})\n' \
        f'\nRated: {respID["Rated"]}' \
        f'\nReleased: {respID["Released"]}' \
        f'\nRuntime: {respID["Runtime"]}' \
        f'\nGenre: {respID["Genre"]}' \
        f'\nCast: {respID["Actors"]}\n' \
        f'\n{respID["Plot"]}'
    bot.send_photo(message.chat.id, respID["Poster"], posterCaption)


def checkResponse(message, response):
    '''
    Error checking method which checks whether the respose from the filter method is empty.

    message is a system message from the bot;
    response is a response from the Filter methos.
    '''
    if "Search" in response.keys() and response["Response"] == "False":
        bot.send_message(message.chat.id, "Sorry, nothing was found")
        return True
    elif "Hits" in response.keys() and len(response["Hits"]) == 0:
        bot.send_message(message.chat.id, "Sorry, nothing was found")
        return True
    else:
        return False


def makeRequestBy(message, token, filterIdent):
    '''
    Searching for a movie using filters: title, year, genre of director. 
    Sends result to the pagination method.

    message is a system message from the bot;
    token is a token of the result page;
    filterIdent is a chosen filter. 
    '''
    querystring = {}
    response = None
    if filterIdent == "Genre":
        requestCount("requestsPerMonth.txt")
        querystring = {"Genres": userMessage.text.capitalize(),
                       "SortBy": "IvaRating",
                       "ProgramTypes": "Movie"}
        response = json.loads(requests.request("GET", config.URLIVA,
                                               headers=config.headersIVA,
                                               params=querystring).text)
    elif filterIdent == "Year":
        requestCount("requestsPerMonth.txt")
        querystring = {"YearRange_Start": userMessage.text,
                       "YearRange_End": userMessage.text,
                       "SortBy": "IvaRating",
                       "ProgramTypes": "Movie"}
        response = json.loads(requests.request("GET", config.URLIVA,
                                               headers=config.headersIVA,
                                               params=querystring).text)
    elif filterIdent == "Director":
        requestCount("requestsPerMonth.txt")
        dir_name = " ".join([name.capitalize()
                             for name in userMessage.text.split(" ")])
        querystring = {"PersonNames": dir_name,
                       "Jobs": "Director",
                       "SortBy": "IvaRating",
                       "ProgramTypes": "Movie"}
        response = json.loads(requests.request("GET", config.URLIVA,
                                               headers=config.headersIVA,
                                               params=querystring).text)
    elif filterIdent == "Name":
        requestCount("requestsPerDay.txt")
        querystring = {"page": str(pageMarker),
                       "r": "json", "s": userMessage.text}
        response = json.loads(requests.request("GET", config.URLIMDB,
                                               headers=config.headersIMDB,
                                               params=querystring).text)
    if len(pagesData[filterIdent][userMessage.text]) < pageMarker:
        if userMessage.text != "/start":
            if checkResponse(message, response):
                return 0
        if token:
            querystring.update({"NextPageToken": token})
        pagesData[filterIdent][userMessage.text].append(response)
        print(response)
        pagination(message, response, filterIdent)
    else:
        print(pagesData[filterIdent][userMessage.text][pageMarker - 1])
        pagination(message, pagesData[filterIdent]
                   [userMessage.text][pageMarker - 1], filterIdent)


def makeRequestByID(message, ID):
    '''
    Sends a result dictionary with the information about the movie.

    message is a system message 
    '''
    requestCount("requestsPerDay.txt")
    querystring = {"i": ID, "r": "json"}
    response = requests.request(
        "GET", config.URLIMDB, headers=config.headersIMDB, params=querystring)
    responseByID = json.loads(response.text)
    print(responseByID)
    sendTitleByID(message, responseByID)


@bot.message_handler(commands=['start'])
def startMessage(message):
    '''
    Greeting message, which pops up after entering /start.
    Starting keyboard with options:
    - Random movie;
    - Search by filter;
    - Top 250;
    - Coming soon in cinema.

    message is a system message fromt the bot.
    '''
    # init keyboard
    keyboard = types.InlineKeyboardMarkup()
    # кнопка поиска по названию
    randomMovieKey = types.InlineKeyboardButton(
        text="Random movie", callback_data="random")
    topKey = types.InlineKeyboardButton(
        text="Top 250 movies link", url=config.TOP250_URL)
    afishaKey = types.InlineKeyboardButton(
        text="Coming soon in cinema", url=config.COMING_SOON_URL)
    filterKey = types.InlineKeyboardButton(
        text="Filters", callback_data="filter")
    keyboard.add(filterKey, topKey, afishaKey, randomMovieKey)
    questionText = """Hi. I'm CinemaBot. I will help you to find information about movie you'd like to know. If it exists, of course. Also I will provide you with helpful links. Moreover, I can even give you an amazing movie to watch right now. You need only to choose the option:"""
    bot.send_message(message.from_user.id, text=questionText,
                     reply_markup=keyboard)


def filterMessage():
    '''
    Keyboard poping after choosing "Search by filter" option..
    Selection keyboard with filters:
    - Title;
    - Genre;
    - Year;
    - Director.
    '''
    keyboard = types.InlineKeyboardMarkup()
    # кнопка поиска по названию
    SearchByTitleKey = types.InlineKeyboardButton(
        text="Search by title", callback_data="SearchByTitle")
    SearchByGenreKey = types.InlineKeyboardButton(
        text="Search by genre", callback_data="SearchByGenre")
    SearchByYearKey = types.InlineKeyboardButton(
        text="Search by year", callback_data="SearchByYear")
    SearchByDirKey = types.InlineKeyboardButton(
        text="Search by director", callback_data="SearchByDir")
    keyboard.add(SearchByTitleKey, SearchByGenreKey,
                 SearchByYearKey, SearchByDirKey)
    return keyboard


def checkMessage(message):
    global userMessage
    while userMessage == None:
        pass


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    '''
    Buttons' worker.
    '''
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
    elif call.data == "filter":
        bot.send_message(call.message.chat.id,
                         "Choose the filter", reply_markup=filterMessage())
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


@bot.message_handler(content_types=['text'])
def getMessageText(message):
    '''
    Processes the user's message to the bot.
    '''
    global userMessage
    userMessage = message


bot.polling(none_stop=True, interval=0)
