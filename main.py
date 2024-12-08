import sqlite3
import logging
import requests
from bs4 import BeautifulSoup

# ======================= Блок 1: Вспомогательные функции =========================
def clean_text(text):
    """Clean and strip text, handling potential None values."""
    return text.strip() if text else ''

# ======================= Блок 2: Парсинг данных с сайта =========================
class WeatherParser:
    def __init__(self, url):
        self.url = url

    def get_weather(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.content, 'html.parser')

        tomorrow_date = "Date not found"
        date_span = soup.find('span', {'class': 'unroll'})
        if date_span:
            select_tag = date_span.find('select', {'id': 'date_selector'})
            if select_tag:
                first_option = select_tag.find('option', {'selected': 'selected'})
                if first_option:
                    tomorrow_date = first_option.text.strip()

        forecast_table = soup.find('table', {'class': 'mesto-predpoved'})
        if not forecast_table:
            logging.warning("Forecast table not found.")
            return [], tomorrow_date

        forecast_data = []
        for row in forecast_table.find_all('tr'):
            tds = row.find_all('td')
            if len(tds) >= 5:
                try:
                    time = clean_text(tds[0].text)
                    weather = clean_text(tds[1].find('img')['alt'] if tds[1].find('img') else '')
                    temperature = clean_text(tds[2].text)
                    precipitation = clean_text(tds[3].text)
                    wind_speed = clean_text(tds[4].text)

                    if time:
                        forecast_data.append({
                            'time': time,
                            'weather': weather,
                            'temperature': temperature,
                            'precipitation': precipitation,
                            'wind_speed': wind_speed,
                        })
                except Exception as e:
                    logging.error(f"Error processing row: {e}")

        return forecast_data, tomorrow_date

# ======================= Блок 3: Работа с базой данных =========================
class WeatherDatabase:
    def __init__(self, db_name="weather.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        # Удалить таблицу, если она существует
        self.cursor.execute("DROP TABLE IF EXISTS Weather")
        # Создать новую таблицу
        self.cursor.execute("""
        CREATE TABLE Weather (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            time TEXT,
            weather TEXT,
            temperature TEXT,
            precipitation TEXT,
            wind_speed TEXT
        )
        """)
        self.conn.commit()

    def insert_weather_data(self, date, forecast_data):
        for entry in forecast_data:
            self.cursor.execute("""
            INSERT INTO Weather (date, time, weather, temperature, precipitation, wind_speed)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (date, entry['time'], entry['weather'], entry['temperature'], entry['precipitation'], entry['wind_speed']))
        self.conn.commit()

    def query_weather(self, date=None, min_temp=None, max_temp=None):
        query = "SELECT * FROM Weather WHERE 1=1"
        params = []

        if date:
            query += " AND date = ?"
            params.append(date)
        if min_temp:
            query += " AND temperature >= ?"
            params.append(min_temp)
        if max_temp:
            query += " AND temperature <= ?"
            params.append(max_temp)

        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()

# ======================= Блок 4: Класс для данных =========================
class DateWeather:
    def __init__(self, date, time, weather, temperature, precipitation, wind_speed):
        self.date = date
        self.time = time
        self.weather = weather
        self.temperature = temperature
        self.precipitation = precipitation
        self.wind_speed = wind_speed

# ======================= Блок 5: Логирование =========================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ======================= Блок 6: Основной код =========================
def main():
    url = "https://www.ventusky.com/ru/dnipropetrovsk"
    parser = WeatherParser(url)
    forecast, tomorrow_date = parser.get_weather()

    if not forecast:
        logging.error("No forecast data available.")
        return

    logging.info("Weather data parsed successfully.")

    db = WeatherDatabase()
    db.insert_weather_data(tomorrow_date, forecast)
    logging.info("Weather data saved to database.")

    query_results = db.query_weather(date=tomorrow_date)
    logging.info("Weather data retrieved from database.")

    print(f"Weather forecast for tomorrow: {tomorrow_date}")
    print(f"{'Time':<7}{'Weather':<25}{'Temperature':<12}{'Precipitation':<15}{'Wind Speed':<10}")
    print("-" * 85)
    for row in query_results:
        print(f"{row[2]:<7}{row[3]:<25}{row[4]:<12}{row[5]:<15}{row[6]:<10}")

    db.close()

if __name__ == "__main__":
    main()
