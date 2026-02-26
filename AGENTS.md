# Agent Guidelines for Boa POS

This document provides guidelines for AI agents working on the `Boa POS` Django project. It includes build/lint/test commands, code style conventions, and project-specific patterns.

## Project Description

**Boa POS** is a simple restaurant order management system designed for small businesses. It handles tables, orders, inventory management, and sales reporting with minimal complexity.

## Project Overview

- **Framework**: Django 5.2.7
- **Database**: SQLite (default)
- **Frontend**: AlpineJS + custom BEM CSS (no build system)
- **Language**: Python 3.12+
- **Locale**: Spanish (Nicaragua) – user-facing strings in Spanish

## Development Philosophy

- **Code Language**: Write all code in English (function names, variable names, class names)
- **Documentation Language**: Write comments, docstrings, and documentation in Spanish
- **User Interface**: The system should be in Spanish (user-facing strings, labels, messages)
- **Simplicity**: Always develop with simplicity and minimalism. Avoid complex or difficult solutions.
- **Practicality**: Focus on practical, working solutions that are easy to understand and maintain.

## Build & Development Commands

### Django Management Commands

```bash
# Run development server
python manage.py runserver

# Apply migrations
python manage.py migrate

# Create new migration files
python manage.py makemigrations

# Run Django shell
python manage.py shell

# Collect static files
python manage.py collectstatic
```

### Testing & Verification

**IMPORTANT**: Do NOT write Python tests for this project. The verification of functionality should be done manually by the developer/user through the browser.

**Verification Protocol**:

1. After making changes, ask the developer to test the functionality directly in the browser
2. Do not create or modify test files (`tests.py`)
3. Focus on ensuring the code works correctly in the actual application context
4. The developer is responsible for verifying that the system functions correctly

If tests need to be run for existing code (though none exist), use Django's built‑in test framework:

```bash
# Run all tests (empty test files exist)
python manage.py test
```

### Linting & Formatting

The project includes Python linting and formatting tools. Run these commands on individual files to ensure code quality (not on the whole project):

```bash
# Format code with Black (for specific files)
black path/to/file.py

# Sort imports with isort (for specific files)
isort path/to/file.py

# Check code style with flake8 (for specific files)
flake8 path/to/file.py --max-line-length=100

# Type checking with mypy (for specific files)
mypy path/to/file.py

# Format HTML templates with djlint (for specific files)
djlint --reformat path/to/template.html
```

**Nota importante**: Los comandos de formateo están separados por lenguaje:

- **Para Python**: usar `black`, `isort`, `flake8`, `mypy`
- **Para HTML**: usar `djlint`
  No mezclar herramientas entre lenguajes (ej. no usar `black` en archivos HTML ni `djlint` en archivos Python).

**Tools installed**:

- **Black 26.1.0** – code formatting
- **isort 8.0.0** – import sorting
- **flake8 7.3.0** – style guide enforcement
- **mypy 1.19.1** – static type checking
- **djlint** – HTML template formatting

Configuration files should be added as needed (`pyproject.toml`, `.flake8`, `.isort.cfg`, `mypy.ini`).

### Frontend Assets

- No build process (CSS/JS are served directly).
- Templates use AlpineJS (CDN) for interactivity; all styling uses custom BEM blocks.
- Custom styles are modular CSS files in `static/css/` (one file per BEM block).
- Prettier is ignored via `.prettierignore`; no Prettier configuration present.

## Code Style Guidelines

### Imports

Group imports in the following order, each group separated by a blank line:

1. Standard library imports
2. Third‑party imports (Django, etc.)
3. Local app imports

Use parentheses for multi‑line imports and break lines after 79 characters.

```python
import csv
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Q

from .models import (
    Ingredient, IngredientMovement, Order, OrderItem, Product,
    ProductCategory, Table
)
```

### Naming Conventions

- **Class names**: `CamelCase` (e.g., `ProductCategory`, `DispatchArea`)
- **Function/method names**: `snake_case` (e.g., `parse_date_range`, `get_total`)
- **Variable names**: `snake_case` (e.g., `total_due`, `order_items`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `UNITS`)

**Language**: All identifiers (class names, function names, variable names) must be in **English**. Only user‑facing strings (labels, messages) should be in Spanish.

### Strings

- Use **double quotes** (`"`) for string literals (including docstrings).
- Use f‑strings for formatting (e.g., `f"Mesa {self.name}"`).
- User‑facing strings should be in **Spanish** (Nicaragua locale). Use Django's `verbose_name` and `verbose_name_plural` in models.

```python
name = models.CharField(max_length=255, unique=True, verbose_name="Nombre")
```

### Models

- Define `__str__` methods that return a human‑readable representation.
- Use `verbose_name` and `verbose_name_plural` for Spanish labels.
- For choices, define a `UNITS`‑like list of 2‑tuples.
- Add custom methods for business logic (e.g., `add_stock`, `apply_movement`).
- Override `save()` when necessary, but call `super().save()`.

Example:

```python
class Ingredient(models.Model):
    UNITS = [
        ("oz", "Onzas"),
        ("lb", "Libras"),
        # ...
    ]

    def add_stock(self, amount):
        self.stock_quantity += Decimal(amount)
        self.save()

    def __str__(self):
        return f"{self.name} ({self.stock_quantity} {self.unit})"
```

### Views

- Use function‑based views with decorators (`@login_required`, `@user_passes_test`).
- Use `get_object_or_404` for retrieving objects.
- Use Django’s `messages` framework for user feedback (success, info, warning, error).
- Use `transaction.atomic` for database operations that must succeed or fail together.
- Annotate queries with `F`, `Sum`, `Q` objects for performance and clarity.
- Use `select_related` and `prefetch_related` to reduce database queries.

### Templates

- Base template: `templates/layout.html`
- Use `{% load static %}` and `{% load user_extras %}` as needed.
- Extend blocks `{% block title %}` and `{% block body %}`.
- Use AlpineJS for simple interactivity; avoid writing complex JavaScript.
- Keep HTML semantic; use custom BEM‑based CSS (see Frontend Guidelines).

### Error Handling

- Use `try`/`except` for expected exceptions (e.g., decimal conversion).
- Display user‑friendly error messages via `messages.error`.
- Let Django handle 404/500 errors (no custom error views defined).

### Comments & Documentation

- Write all comments and docstrings in **Spanish**.
- Use **section headers** with emojis to group related code blocks.
- Write docstrings for functions and classes (in Spanish).
- Use inline comments sparingly; prefer clear variable and function names.

Example:

```python
# ==========================
# 🧾 INVENTARIO Y MOVIMIENTOS
# ==========================
```

## Frontend Guidelines

Detailed frontend specifications are documented in [`docs/frontend.md`](docs/frontend.md). Key points:

### Architecture

- **Interactivity**: Use AlpineJS for simple interactivity; avoid custom JavaScript when possible.
- **JavaScript**: If required, place in `static/js/` with descriptive filenames.
- **Styles**: Pure CSS with BEM methodology (Block, Element, Modifier). **PicoCSS has been removed**; all styling uses custom BEM blocks.
- **Template extensions**: Use `{% block extra_css %}` and `{% block extra_js %}` in templates to add page-specific assets.

### CSS Structure

- **Directory**: `static/css/` – one file per BEM block.
- **Naming**: Bloques reutilizables con nombres **semánticos y funcionales**, no genéricos, utilitarios ni específicos para una plantilla. Los nombres deben describir el propósito del componente, no su apariencia o ubicación.
  - **Correcto**: `.card`, `.toolbar`, `.ads`, `.grid`, `.messages`, `.list` (componentes reutilizables)
  - **Incorrecto**: `.create-order`, `.auth`, `.new-table` (específicos de página), `.text-small`, `.mt-1`, `.p-1` (clases utilitarias)
- **Theming**: Support light/dark themes using CSS variables and `prefers-color-scheme`.
- **File organization**: Each block documented with its purpose at the top.

### BEM Convention

- **Block**: `.miBloque` (independent component)
- **Element**: `.miBloque__suElemento` (part of a block)
- **Modifier**: `.miBloque--suModificador` (variant)

### Maintenance

- When creating new CSS blocks/files, update `docs/frontend.md` and this `AGENTS.md`.
- Ensure new CSS files are available in `static/css/` for selective import. Optionally, add them to `static/css/styles.css` for bundling.

## Environment & Configuration

- Environment variables are loaded from `.secret` (see `core/settings.py`).
- The `.env` directory contains the Python virtual environment; always activate it before running any Python commands (e.g., `source .env/bin/activate`).
- Database is SQLite (`db.sqlite3`); keep it out of version control.

## CI/CD

No continuous integration pipeline is configured. If adding one, consider:

- Running Django tests
- Checking for missing migrations (`python manage.py makemigrations --check`)
- Linting with `flake8` (now available)
- Formatting with `black` (now available)

## Additional Notes

- **Cursor/Copilot rules**: No `.cursorrules`, `.cursor/rules/`, or `.github/copilot-instructions.md` files present.
- **Git hooks**: No pre‑commit or pre‑push hooks configured.
- **Dependencies**: Listed in `requirements.txt`; core Django packages plus linting/formatting tools (black, flake8, isort, mypy).
- **Static files**: Served from `static/` directory; no CDN besides AlpineJS.

## Summary for Agents

1. **DO NOT write Python tests** – ask the developer to test functionality directly in the browser.
2. Write **code in English**, **comments/documentation in Spanish**.
3. Keep the **user interface in Spanish** (labels, messages, `verbose_name`).
4. Develop with **simplicity and minimalism** – avoid complex solutions.
5. Follow the existing import grouping and string style (double quotes).
6. Use Django’s built‑in utilities (`get_object_or_404`, `messages`, `transaction.atomic`).
7. Keep frontend changes minimal – this is a server‑side Django application.
8. When in doubt, mimic the patterns found in `orders/views.py` and `orders/models.py`.
9. Run linting and formatting commands on individual files (`black path/to/file.py`, `flake8 path/to/file.py`, `djlint --reformat path/to/template.html`, etc.) after making changes to ensure code quality.
10. When working on HTML, CSS, or JavaScript, always review `docs/frontend.md` for context on frontend architecture and BEM methodology.
11. Always activate the virtual environment (`.env/bin/activate`) before running any Python commands.

---

_Last updated: 2026‑02‑26_
