import aiohttp
import asyncio
import time
import datetime
import requests

# Сопоставление месяцев с сезонами
month_to_season = {12: "winter", 1: "winter", 2: "winter",
                   3: "spring", 4: "spring", 5: "spring",
                   6: "summer", 7: "summer", 8: "summer",
                   9: "autumn", 10: "autumn", 11: "autumn"}

# Использование OpenWeatherMap API для получения текущей температуры города
def get_city_weather(API_KEY, city):
    URL = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric'
    response = requests.get(URL)
    current_datetime = datetime.datetime.now()

    if response.status_code == 200:
        data = response.json()
        temperature = data['main']['temp']
        return temperature, current_datetime
    else:
        raise Exception(f"Ошибка при получении данных о погоде: {response.status_code} - {response.text}")

# Асинхронное обращение к API
async def get_city_weather_async(API_KEY, city, session):
    URL = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric'
    async with session.get(URL) as response:
        current_datetime = datetime.datetime.now()
        if response.status == 200:
            data = await response.json()
            temperature = data['main']['temp']
            return temperature, current_datetime
        else:
            raise Exception(f"Ошибка при получении данных о погоде: {response.status} - {await response.text()}")

# функция определения: является ли текущая температура нормальной, исходя из исторических данных для текущего сезона.
def is_temperature_normal(city, current_temp, current_datetime, season_profile):
    current_month = current_datetime.month
    current_season = month_to_season.get(current_month)
    season_profile = season_profile[season_profile.index == current_season]

    if current_season in season_profile.index:
        mean_temp = season_profile.loc[current_season, 'mean']
        std_temp = season_profile.loc[current_season, 'std']

        # Диапазон нормальной температуры
        lower_bound = mean_temp - 2 * std_temp
        upper_bound = mean_temp + 2 * std_temp

        # Проверка нормальности температуры
        return lower_bound <= current_temp <= upper_bound
    else:
        raise ValueError(f"Нет данных для города {city} и сезона {current_season}")

# Сравнение времени выполнения
async def compare_execution_times(API_KEY, cities):
    # Синхронный вызов
    start_time = time.time()
    for city in cities:
        cur_temp, cur_datetime = get_city_weather(API_KEY, city)
    sync_duration = time.time() - start_time

    # Асинхронный вызов
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        tasks = [get_city_weather_async(API_KEY, city, session) for city in cities]
        async_results = await asyncio.gather(*tasks)
    async_duration = time.time() - start_time

    # Итоговое сравнение
    print("Результаты сравнения:")
    print(f"Синхронный метод: {sync_duration:.2f} секунд")
    print(f"Асинхронный метод: {async_duration:.2f} секунд")
    print(f"Синхронный метод быстрее!" if sync_duration < async_duration else "Асинхронный метод быстрее!")