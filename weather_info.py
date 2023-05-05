import datetime
from collections import defaultdict, Counter

import requests

city_ID = 554234
API_key = '1459276c332aeb56859cce6b571c9d5b'
resp = requests.get(f'http://api.openweathermap.org/data/2.5/forecast',
                    params={
                        'id': {city_ID},
                        'appid': {API_key},
                        'units': 'metric'})

weather_info = resp.json()

tomorrow = datetime.datetime.today() + datetime.timedelta(days=1)

weather_dict = {"broken clouds": "облачно", "scattered clouds": "облачно", "overcast clouds": "пасмурно",
                "few clouds": "малооблачно", "clear sky": "ясно",
                "light rain": "слабый дождь", "light snow": "слабый снег"}


def wind_drctn(degrees):
    if 348 <= degrees <= 360 or 0 <= degrees < 12:
        return "Северный"
    elif 12 <= degrees < 34:
        return "ССВ"
    elif 34 <= degrees < 56:
        return "СВ"
    elif 56 <= degrees < 79:
        return "BCB"
    elif 79 <= degrees < 101:
        return "Восточный"
    elif 101 <= degrees < 123:
        return "ВЮВ"
    elif 123 <= degrees < 145:
        return "ЮВ"
    elif 145 <= degrees < 170:
        return "ЮЮВ"
    elif 170 <= degrees < 192:
        return "Южный"
    elif 192 <= degrees < 214:
        return "ЮЮЗ"
    elif 214 <= degrees < 236:
        return "ЮЗ"
    elif 236 <= degrees < 258:
        return "ЗЮЗ"
    elif 258 <= degrees < 282:
        return "Западный"
    elif 282 <= degrees < 304:
        return "ЗСЗ"
    elif 304 <= degrees < 326:
        return "СЗ"
    elif 326 <= degrees < 348:
        return "ССЗ"


class Weather:

    @staticmethod
    def weather_now():
        info = weather_info['list'][0]
        time_now = datetime.datetime.strftime(datetime.datetime.now(), "%d-%m-%Y %H:%M:%S")
        pressure_raw = int(info['main']['pressure']) * 0.750062
        time = f"Время: {time_now}\n"
        temp = f"Температура: {info['main']['temp']} C"
        feels_like = f"Ощущается как: {info['main']['feels_like']} С"
        pressure = f"Давление: {pressure_raw} мм рт ст"
        humidity = f"Влажность: {info['main']['humidity']}%"
        wind = f"Ветер: {info['wind']['speed']} м\с"
        wind_dir = f"Направление ветра: {wind_drctn(int(info['wind']['deg']))}"
        visibility = f"Видимость: {info['visibility']} м"
        if info['weather'][0]['description'] in weather_dict:
            cloudy = f"Облачность: {weather_dict[info['weather'][0]['description']]}"
        else:
            cloudy = f"Облачность: {info['weather'][0]['description']}"
        return time, temp, feels_like, pressure, humidity, cloudy, wind, wind_dir, visibility

    @staticmethod
    def weather_on_day(today=False):

        if today == True:
            day = datetime.date.strftime(datetime.datetime.today(), "%Y-%m-%d")
        else:
            day = datetime.date.strftime(tomorrow.date(), "%Y-%m-%d")

        datetime_lst = [f"{day} 06:00:00", f"{day} 09:00:00", f"{day} 12:00:00",
                        f"{day} 15:00:00", f"{day} 18:00:00", f"{day} 21:00:00"]

        weather_lst = [f"Дата: {day}"]

        for info in weather_info['list']:
            if info['dt_txt'] in datetime_lst:
                time_raw = info['dt_txt'].split(" ")[1]
                time = f"{time_raw}"
                temp = f"Температура: {info['main']['temp']} C"
                feels_like = f"Ощущается как: {info['main']['feels_like']} С"
                wind = f"Ветер: {info['wind']['speed']} м\с"
                if info['weather'][0]['description'] in weather_dict:
                    cloudy = f"Облачность: {weather_dict[info['weather'][0]['description']]}"
                else:
                    cloudy = f"Облачность: {info['weather'][0]['description']}"
                weather_lst.append(f"{time}\n{temp}\n{feels_like}\n{cloudy}\n{wind}")
        return weather_lst

    @staticmethod
    def weather_on_several():
        several_days_temp = defaultdict(list)
        several_days_weather_type = defaultdict(list)
        several_days_wind = defaultdict(list)
        weather_dict_per_date = defaultdict(list)
        final_list = []

        for info in weather_info['list']:
            date = info['dt_txt'].split()[0]
            temp = info['main']['temp']
            wind = info['wind']['speed']
            if info['weather'][0]['description'] in weather_dict:
                cloudy = weather_dict[info['weather'][0]['description']]
            else:
                cloudy = info['weather'][0]['description']

            several_days_temp[date].append(temp)
            several_days_weather_type[date].append(cloudy)
            several_days_wind[date].append(wind)

        for k, v in several_days_weather_type.items():
            weather_per_day = Counter(v)
            most_common = weather_per_day.most_common(1)
            weather_dict_per_date[k].append(f"{most_common[0][0]}\n")

        for k, v in several_days_temp.items():
            weather_dict_per_date[k].append(f"Температура: {min(v)}-{max(v)} С\n")


        for k, v in several_days_wind.items():
            weather_dict_per_date[k].append(f"Ветер: {min(v)}-{max(v)} м/с\n")

        for k, v in weather_dict_per_date.items():
            t, c, w = v
            string = f"Дата: {k} {t}{c}{w}"
            final_list.append(string)

        return "\n".join(final_list)



if __name__ == '__main__':
    Weather().weather_now()
    Weather().weather_on_day(today=True)
    Weather.weather_on_several()