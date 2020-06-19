# -*- coding: utf-8 -*-
token = '1107504191:AAFKdrsCNgf5rZLfIl0woHZVWD0VxYZ5FxU'

headersIMDB = {
    'x-rapidapi-host': "movie-database-imdb-alternative.p.rapidapi.com",
    'x-rapidapi-key': "33e34af31fmsh45e531bff2a7970p1f7d96jsn6a0c3e75f69d"
    }
headersIVA = {
        'x-rapidapi-host': "ivaee-internet-video-archive-entertainment-v1.p.rapidapi.com",
        'x-rapidapi-key': "33e34af31fmsh45e531bff2a7970p1f7d96jsn6a0c3e75f69d",
        'content-type': "application/json"
        }

URLIMDB = "https://movie-database-imdb-alternative.p.rapidapi.com/"
URLIVA = "https://ivaee-internet-video-archive-entertainment-v1.p.rapidapi.com/entertainment/search/"

TOP250_URL = "http://www.imdb.com/chart/top"
COMING_SOON_URL = "https://www.imdb.com/movies-coming-soon/"

top250_id = []
coming_soon_id = []


# too slow
# def get_top250(url=TOP250_URL):
#     '''
#     Gives the top 250 movies from IMDb rate.
#     Returns a list of IDs:
#     url is a url of the resource from which top is taken.
#     By default, it's IMDb url.
#     '''
#     global top250_id
#     r = requests.get(url)
#     html = r.text.split("\n")
#     for line in html:
#         line = line.rstrip("\n")
#         m = re.search(r'data-titleid="tt(\d+?)"', line)
#         if m:
#             _id = m.group(1)
#             top250_id.append(_id)
#     top250_id = list(set(top250_id))
#     return top250_id


# def get_coming_soon(url=config.COMING_SOON_URL):
#     '''
#     Gives the coming soon movies infrotmation.
#     Returns a dictionary with 2 key-value pairs:
#     - 'Search' : list of dictionaries each containing:
#         - title of the movie;
#         - year of release;
#         - imdb ID.
#     - 'totalResult' : number of found results.
#     url is a url of the resource from which upcomings are taken.
#     By default, it's IMDb url.
#     '''
#     global coming_soon_id
#     # current date: 2020-06-01 in format 2020-06
#     d = str(datetime.date.today())[:7]
#     r = requests.get(url+d)
#     html = r.text.split("\n")
#     for line in html:
#         line = line.rstrip("\n")
#         m = re.search(r'<a href="/title/tt(\d+)/"', line)
#         if m:
#             _id = m.group(1)
#             coming_soon_id.append(_id)
#     coming_soon_id = list(set(coming_soon_id))

#     return coming_soon_id


# def getDict(movies_id: list, page=1):
#     '''
#     Add description.
#     movies_id is a list of movie IDs from IMDb. IDs must be strings in format '010201'.
#     page by default is 1, ignored if length of movies_id is less than 10.
#     '''
#     ia = IMDb()
#     result_dict = {"Search": [], "totalResults": len(movies_id)}

#     if len(movies_id) > 10:
#         proper_ids = movies_id[(page-1)*10:(page*10)]
#     else:
#         proper_ids = movies_id

#     for index in range(len(proper_ids)):
#         movie = ia.get_movie(proper_ids[index])
#         m_id = "tt{0}".format(proper_ids[index])
#         title = movie['title']
#         year = str(movie['year'])
#         tmp = {"Title": title, "Year": year, "imdbID": m_id}
#         result_dict["Search"].append(tmp)

#     return result_dict
