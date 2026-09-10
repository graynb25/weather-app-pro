# Coding Standards

## General

- One class = one responsibility.
- One method = one task.
- Keep methods under ~40 lines when practical.
- Avoid duplicate code.
- Use descriptive names.

## Widgets

Widgets never call APIs.

Widgets never perform business logic.

Widgets only display data.

## Managers

Managers never create UI.

Managers only manage resources.

## Services

Services only communicate with external APIs.

## UI

UI assembles widgets.

UI never performs calculations.

## Comments

Explain WHY.

Avoid comments that only explain WHAT.

## Docstrings

Every public class and public method should have one.