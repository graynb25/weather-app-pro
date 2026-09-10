# Weather App Pro

A desktop weather application for Windows built with Python and PyQt5. It
retrieves current conditions and a 5-day forecast from the OpenWeatherMap API
and presents them with SVG icons, Lottie animations, and QSS themes.

## Features

- Search weather by city
- Current temperature in Fahrenheit and Celsius
- Feels like, humidity, wind, visibility, and pressure tiles
- Minimum and maximum temperature
- 5-day forecast cards with weather icons
- Live local clock for the selected city
- Country flag for the searched city
- Animated Lottie weather and detail icons
- Light and dark QSS themes
- Error handling for empty input, unknown cities, and network problems

## Requirements

- Python 3.14 or newer
- An OpenWeatherMap API key (the free tier is enough)
- Dependencies, pinned in `requirements.txt`:
  - PyQt5 5.15.11
  - requests 2.32.5
  - python-dotenv 1.2.2

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and set your key:
   ```text
   OPENWEATHER_API_KEY=your_key_here
   ```
   Never commit `.env`. It is already listed in `.gitignore`.
4. Run the app:
   ```bash
   python main.py
   ```

To test the Lottie animation pipeline on its own: `python test_lottie.py`

## Project Structure

```
weather-app-pro/
│
├── main.py                  Entry point
├── ui.py                    Main window, layouts, signals, display logic
├── weather_api.py           OpenWeatherMap client
├── weather_model.py         WeatherData and ForecastData dataclasses
├── config.py                App constants
├── utils.py                 Conversion helpers
├── forecast_card.py         One forecast day card
│
├── managers/                IconManager, AnimationManager, FlagManager, ThemeManager
├── widgets/                 DetailCard, forecast widget, LottieWidget
├── resources/               Icons, Lottie animations, QSS themes, lottie player
├── docs/                    Improvement plans (error handling, security, testing, redesign)
├── old/                     Legacy code, reference only
├── test_lottie.py           Manual animation test harness
├── .env.example             Template for the required environment variables
└── requirements.txt         Pinned dependencies
```

`agent.md` holds the working rules for this project. Anyone (human or AI)
changing the code should read it first.

## Planned Features

These exist as empty placeholder files already:

- Saved cities (`favorites.py`, `favorites.json`)
- Persisted settings such as units and theme (`settings.py`, `settings.json`)
- Painter-based weather effects (`widgets/weather_animation.py`)
- An automated pytest suite (plan in `docs/testing-plan.md`)
- Condition-based themes: `sunny`, `cloudy`, `rainy`, and `snowy` stylesheets
  exist but the menu currently offers only light and dark

The improvement roadmap lives in `docs/`.

## Technologies

- Python 3.14
- PyQt5 (Widgets, Svg, WebEngine)
- requests
- python-dotenv
- OpenWeatherMap API

## License

This project is licensed under the MIT License.
