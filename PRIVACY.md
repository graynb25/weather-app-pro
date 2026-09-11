# Privacy

Weather App Pro collects nothing. There is no account, no telemetry,
no analytics, and no developer-side server.

## What leaves your machine

- The city names you search are sent to OpenWeatherMap
  (https://openweathermap.org/) over HTTPS to fetch weather data.
- Your own OpenWeatherMap API key is sent with every request, also to
  OpenWeatherMap only.

Those requests are subject to OpenWeatherMap's own terms and privacy
policy: https://openweathermap.org/privacy-policy

## What stays on your machine

Everything else is stored locally in your app data folder
(%LOCALAPPDATA%\WeatherAppPro for an installed copy; the project
folder when running from source):

- Your API key (plain text, dotenv format; never transmitted anywhere
  except to OpenWeatherMap)
- settings.json (units, condition mode, refresh interval, window
  position)
- favorites.json (your saved cities)
- cache.json (the last successful search)
- logs/app.log (rotating log of app events; URLs are redacted before
  they are written)

## Uninstalling

The uninstaller leaves this folder in place by default. Delete
%LOCALAPPDATA%\WeatherAppPro to remove everything, including your key.

## Disclaimer

Weather data is provided by OpenWeatherMap with no accuracy warranty.
Do not rely on it for safety-critical decisions. This application is
provided "as is" (see LICENSE).
