import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from analysis.data_analysis import analyze_city
from api.weather_api import get_city_weather, is_temperature_normal

st.title("Анализ и мониторинг погоды")

st.sidebar.header("Настройки")
uploaded_file = st.sidebar.file_uploader("Загрузите CSV файл с историческими данными", type=["csv"])

if uploaded_file:
    data = pd.read_csv(uploaded_file, parse_dates=['timestamp'])
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data = data.sort_values('timestamp').reset_index(drop=True)
    cities = data['city'].unique()

    # Выбор города
    city = st.sidebar.selectbox("Выберите город", cities)

    # Результаты анализа для выбранного города
    city_results = analyze_city(data, city)

    # Извлечение данных анализа
    trend_slope = city_results['trend_slope']
    avg_temp = city_results['avg_temp']
    min_temp = city_results['min_temp']
    max_temp = city_results['max_temp']
    season_profile = city_results['season_profile']
    season_roll_profile = city_results['season_roll_profile']
    anomalies = city_results['anomalies']
    city_data = city_results['city_data']

    # Описательная статистика
    with st.expander(f"Описательная статистика для {city}"):
        st.write(f"Средняя температура: {round(avg_temp, 2)}°C")
        st.write(f"Минимальная температура: {round(min_temp, 2)}°C")
        st.write(f"Максимальная температура: {round(max_temp, 2)}°C")

    # API для текущей температуры
    st.subheader("Текущая погода")
    api_key = st.text_input("Введите API ключ OpenWeatherMap", type="password")
    if api_key:
        try:
            # Получение текущей температуры
            current_temp, current_datetime = get_city_weather(api_key, city)
            st.write(f"Текущая температура в городе {city}: {current_temp}°C")

            # Проверка, нормальна ли температура для текущего сезона
            is_temp_normal = is_temperature_normal(city, current_temp, current_datetime, season_profile)
            if is_temp_normal:
                st.write(f"Текущая температура ({current_temp}) в городе {city} является нормальной в пределах текущего сезона.")
            else:
                st.write(f"Текущая температура ({current_temp}) в городе {city} не является нормальной в пределах текущего сезона.")

        except Exception as e:
            if "401" in str(e):
                st.error(e)
            elif "404" in str(e):
                st.error("Город не найден.")
            else:
                st.error(f"Произошла ошибка: {e}")
                
    # График временного ряда температур с выделением аномалий
    city_data['rolling_avg'] = city_data['temperature'].rolling(window=30).mean()  # Среднее за 30 дней
    st.subheader("Временной ряд температур")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(city_data['timestamp'], city_data['temperature'], label="Температура", color='blue')
    ax.scatter(anomalies['timestamp'], anomalies['temperature'], color='red', label="Аномалии", zorder=5)
    ax.plot(city_data['timestamp'], city_data['rolling_avg'], label="Скользящее среднее (30 дней)", color='orange', linestyle='-')
    ax.set_title("Временной ряд температур")
    ax.set_xlabel("Дата")
    ax.set_ylabel("Температура")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # Отображение аномалий
    st.subheader("Аномалии")
    if not anomalies.empty:
        st.dataframe(anomalies[['city','timestamp', 'temperature']])
    else:
        st.write("Аномалий не обнаружено.")

    # График сезонного профиля
    st.subheader("Сезонный профиль температуры")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(
        season_profile.index,
        season_profile['mean'],
        yerr=season_profile['std'],
        fmt='o',
        label='Средняя температура в пределах ст. откл.',
        color='orange'
    )
    ax.set_title("Сезонный профиль")
    ax.set_xlabel("Сезон")
    ax.set_ylabel("Температура")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # График скользящего среднего для сезонного профиля
    st.subheader("Скользящее среднее сезонного профиля")
    fig, ax = plt.subplots(figsize=(10, 6))
    if 'season_roll_mean' in city_data.columns and 'season_roll_std' in city_data.columns:
        ax.plot(city_data['timestamp'], city_data['season_roll_mean'], color='purple', label='Скользящее среднее')
        ax.fill_between(
            city_data['timestamp'],
            city_data['season_roll_mean'] - city_data['season_roll_std'],
            city_data['season_roll_mean'] + city_data['season_roll_std'],
            color='lightblue',
            alpha=0.5,
            label='Стандартное отклонение'
        )
        ax.set_title("Сезонный профиль (скользящее среднее)")
        ax.set_xlabel("Дата")
        ax.set_ylabel("Температура")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

    # Гистограмма распределения температур
    st.subheader("Гистограмма распределения температур")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(city_data['temperature'], bins=30, color='skyblue', edgecolor='black')
    ax.set_title(f"Гистограмма распределения температур в городе {city}")
    ax.set_xlabel("Температура")
    ax.set_ylabel("Частота")
    ax.grid(True)
    st.pyplot(fig)

    # Тренд температуры
    st.subheader("Оценка тренда температуры")

    # Вычисление линии тренда на основе trend_slope
    start_temp = city_data['temperature'].iloc[0]  # Начальная температура
    start_date = city_data['timestamp'].iloc[0]  # Начальная дата

    # Расчет тренда с учетом начальной температуры и тренда
    trend_y = start_temp + trend_slope * (city_data['timestamp'] - start_date).dt.days

    # Отображение тренда
    if trend_slope > 0:
        st.write(f"Тренд положительный: температура увеличивается на {round(trend_slope, 5)}°C/день "
                f"или {round(trend_slope * 365, 2)}°C/год.")
    elif trend_slope < 0:
        st.write(f"Тренд отрицательный: температура уменьшается на {round(trend_slope, 5)}°C/день "
                f"или {round(trend_slope * 365, 2)}°C/год.")
    else:
        st.write("Температура остается неизменной.")

    # График с трендовой линией
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(city_data['timestamp'], city_data['temperature'], label="Температура", color='blue')
    ax.plot(city_data['timestamp'], trend_y, label="Линия тренда", color='red', linestyle='--')
    ax.set_title("Временной ряд температур с линией тренда")
    ax.set_xlabel("Дата")
    ax.set_ylabel("Температура")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

else:
    st.write("Данные отсутсвуют. Загрузите файл с историческими данными в настройках.")