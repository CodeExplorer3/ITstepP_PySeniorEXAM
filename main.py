import requests
from bs4 import BeautifulSoup


def clean_text(text):
    """Clean and strip text, handling potential None values."""
    return text.strip() if text else ''


def get_weather():
    url = "https://www.ventusky.com/ru/dnipropetrovsk"  # Replace with actual URL
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract tomorrow's date
    tomorrow_date = "Date not found"
    date_span = soup.find('span', {'class': 'unroll'})
    if date_span:
        select_tag = date_span.find('select', {'id': 'date_selector'})
        if select_tag:
            first_option = select_tag.find('option', {'selected': 'selected'})
            if first_option:
                tomorrow_date = first_option.text.strip()

    # Find the table containing the forecast for the next 24 hours
    forecast_table = soup.find('table', {'class': 'mesto-predpoved'})
    if not forecast_table:
        print("Forecast table not found.")
        return [], tomorrow_date

    forecast_data = []
    for row in forecast_table.find_all('tr'):
        tds = row.find_all('td')
        if len(tds) >= 5:
            try:
                # Carefully extract each piece of information
                time = clean_text(tds[0].text)
                weather = clean_text(tds[1].find('img')['alt'] if tds[1].find('img') else '')
                temperature = clean_text(tds[2].text)
                precipitation = clean_text(tds[3].text)
                wind_speed = clean_text(tds[4].text)

                # Only add if we have a valid time
                if time:
                    forecast_data.append({
                        'time': time,
                        'weather': weather,
                        'temperature': temperature,
                        'precipitation': precipitation,
                        'wind_speed': wind_speed,
                    })
            except Exception as e:
                print(f"Error processing row: {e}")

    return forecast_data, tomorrow_date


def main():
    # Get and print weather data
    forecast, tomorrow_date = get_weather()

    if not forecast:
        print("No forecast data available.")
        return

    # Print header with tomorrow's date
    print(f"Weather forecast for tomorrow: {tomorrow_date}")

    # Header row with proper formatting
    print(f"{'Time':<7}{'Weather':<25}{'Temperature':<12}{'Precipitation':<15}{'Wind Speed':<10}")
    print("-" * 85)

    # Loop through forecast and format each row for readability
    for hour in forecast:
        print(
            f"{hour['time']:<7}{hour['weather']:<25}{hour['temperature']:<12}{hour['precipitation']:<15}{hour['wind_speed']:<10}")


if __name__ == "__main__":
    main()