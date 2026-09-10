# Weather App Pro Architecture

## Overview

Weather App Pro is built using PyQt5 with a modular architecture.

The project separates:

- UI
- Business logic
- Weather services
- Resource managers
- Reusable widgets

This keeps each module focused on one responsibility.

---

## Folder Structure

main.py
ui.py

models/
services/
managers/
widgets/
styles/
resources/
docs/

---

## Data Flow

User

↓

WeatherService

↓

WeatherModel

↓

WeatherApp

↓

Widgets

---

## Managers

AnimationManager

- Weather animations
- Detail animations

IconManager

- Weather SVG icons
- Detail SVG icons

ThemeManager

- Dark theme
- Light theme

---

## Widgets

DetailCard

Displays

- icon
- title
- value

ForecastCard

Displays

- day
- icon
- temperatures

LottieWidget

Displays animated weather icons.

---

## Design Principles

- One class = one responsibility.
- One method = one task.
- Reusable widgets.
- Minimal business logic inside the UI.