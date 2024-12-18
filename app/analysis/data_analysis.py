from sklearn.linear_model import LinearRegression
import pandas as pd
import time
import matplotlib.pyplot as plt
import seaborn as sns

def analyze_city(df, city):
    # Фильтрация данных по городу
    city_data = df[df['city'] == city].copy()

    # Скользящее среднее и стандартное отклонение
    city_data['30_day_roll_mean'] = city_data['temperature'].rolling(window=30).mean()
    city_data['30_day_roll_std'] = city_data['temperature'].rolling(window=30).std()

    # Аномалии
    city_data['anomaly'] = (city_data['temperature'] - city_data['30_day_roll_mean']).abs() > 2 * city_data['30_day_roll_std']
    anomalies = city_data[city_data['anomaly']]

    # Профиль сезона
    season_profile = city_data.groupby('season')['temperature'].agg(['mean', 'std'])

    # Сезонный профиль с учетом скользящего окна
    city_data['season_roll_mean'] = city_data.groupby('season')['temperature'].rolling(window=30).mean().reset_index(level=0, drop=True)
    city_data['season_roll_std'] = city_data.groupby('season')['temperature'].rolling(window=30).std().reset_index(level=0, drop=True)
    season_roll_profile = city_data.groupby('season')[['season_roll_mean', 'season_roll_std']].agg(['mean', 'std'])

    # Линейная регрессия
    city_data['timestamp'] = pd.to_datetime(city_data['timestamp'])
    city_data['days'] = (city_data['timestamp'] - city_data['timestamp'].min()).dt.days
    X = city_data[['days']]
    y = city_data['temperature']
    model = LinearRegression()
    model.fit(X, y)
    trend_slope = model.coef_[0]

    # Основные показатели температуры
    avg_temp = city_data['temperature'].mean()
    min_temp = city_data['temperature'].min()
    max_temp = city_data['temperature'].max()

    return {
        'city': city,
        'trend_slope': trend_slope,
        'avg_temp': avg_temp,
        'min_temp': min_temp,
        'max_temp': max_temp,
        'season_profile': season_profile,
        'season_roll_profile': season_roll_profile,
        'anomalies': anomalies,
        'city_data': city_data
    }

# Последовательный режим
def analyze_cities_sequential(df, cities):
    results = []
    start_time = time.time()
    
    for city in cities:
        result = analyze_city(df, city)
        results.append(result)
    
    elapsed_time = time.time() - start_time
    return results, elapsed_time

# Визуализация анализа города
def display_city_analysis(results):
    city = results['city']
    trend_slope = results['trend_slope']
    avg_temp = results['avg_temp']
    min_temp = results['min_temp']
    max_temp = results['max_temp']
    season_profile = results['season_profile']
    season_roll_profile = results['season_roll_profile']
    anomalies = results['anomalies']
    city_data = results['city_data']

    print(f"Город: {city}")
    print(f"Средняя температура: {round(avg_temp, 2)}°C")
    print(f"Минимальная температура: {round(min_temp, 2)}°C")
    print(f"Максимальная температура: {round(max_temp, 2)}°C")
    print("\nПрофиль сезона:")
    print(season_profile.to_string())

    if trend_slope > 0:
      print(f"\nТренд положительный, температура постепенно увеличивается на: {round(trend_slope, 5)}°C/день или {round(trend_slope, 5) * 365}°C/год")
    elif trend_slope < 0:
      print(f"\nТренд отрицательный, температура постепенно уменьшается на: {round(trend_slope, 5)}°C/день или {round(trend_slope, 5) * 365}°C/год")
    else:
      print(f"\nТренд находится в 0, температура не изменяется")

    print("\nАномалии:")
    if not anomalies.empty:
        print(anomalies[['season', 'timestamp', 'temperature']])
    else:
        print("Аномалии не обнаружены.")

    # Визуализация аномалий
    if not anomalies.empty:
        plt.figure(figsize=(10, 6))
        plt.plot(anomalies['timestamp'], anomalies['temperature'], 'ro', label='Аномалии')
        plt.title(f"Аномалии в температуре для города {city}")
        plt.xlabel('Дата')
        plt.ylabel('Температура')
        plt.grid(True)
        plt.legend()
        plt.show()

    # Визуализация профиля сезона
    plt.figure(figsize=(10, 6))
    plt.bar(season_profile.index, season_profile['mean'], yerr=season_profile['std'], capsize=5)
    plt.title(f"Профиль температуры по сезонам для города {city}")
    plt.xlabel('Сезон')
    plt.ylabel('Температура')
    plt.grid(True)
    plt.show()

    # Визуализация профиля сезона с учетом скользящего окна
    plt.figure(figsize=(10, 6))
    plt.bar(season_roll_profile.index, season_roll_profile['season_roll_mean']['mean'],
            yerr=season_roll_profile['season_roll_mean']['std'], capsize=5)
    plt.title(f"Профиль температуры по сезонам (скользящее окно) для города {city}")
    plt.xlabel('Сезон')
    plt.ylabel('Температура (среднее по скользящему окну)')
    plt.grid(True)
    plt.show()

    # Сезонное распределение температуры
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='season', y='temperature', data=city_data)
    plt.title(f"Сезонное распределение температуры для города {city}")
    plt.xlabel('Сезон')
    plt.ylabel('Температура')
    plt.grid(True)
    plt.show()