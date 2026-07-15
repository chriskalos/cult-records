# Cult Records

Cult Records is a Django web application for browsing and managing a record catalogue.

## Current functionality

The home page uses a reusable Bootstrap layout with shared header and footer templates. It displays a responsive product list populated from database records.

Public users can search the catalogue from the site header or the search page. Search terms are matched against product titles, artists, and descriptions, with relevant results ranked first. The search allows reasonable misspellings and words that appear across more than one product field.

Search results can be filtered by artist, product type, minimum price, and maximum price. Price filtering uses a dual-ended slider with editable values. Its range starts at zero and ends at the highest product price currently in the catalogue. Filters apply automatically when changed, with a short delay for price input. The filters appear in a left sidebar on larger screens and stack above the results on smaller screens.

The product database model stores an optional image URL, artist, title, description, product type, and price. Product types are limited to LP, CD, bundle, and merch.

Each product uses a manually assigned uppercase alphanumeric product ID as its primary key.

An initial data migration adds four placeholder products for development.

## Local setup

Cult Records requires Python 3.13 or newer. `uv` is optional. A standard Python virtual environment is enough to run the project.

### Windows with standard Python

Install Python 3.13 from the [Python website](https://www.python.org/downloads/windows/) if it is not already installed. Keep the Python launcher selected during installation.

Open Command Prompt or PowerShell in the project folder, then run:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py runserver
```

Open <http://127.0.0.1:8000/> in a browser. Press `Ctrl+C` in the terminal to stop the server.

These commands call the virtual environment's Python directly, so activating the environment is not required.

### macOS or Linux with standard Python

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

### Setup with uv

Install `uv` using the [official installation guide](https://docs.astral.sh/uv/getting-started/installation/), then run:

```bash
uv sync --locked
uv run python manage.py migrate
uv run python manage.py runserver
```

The project uses `uv` during development because it creates and manages the virtual environment, installs dependencies quickly, and keeps exact versions in `uv.lock`. The standard Python instructions use `requirements.txt`, which contains the same resolved dependency versions, so `uv` is not needed to run the application.

When dependencies change, update `uv.lock` first and refresh the compatibility file with:

```bash
uv export --format requirements-txt --no-emit-project --no-hashes --no-annotate --output-file requirements.txt
```
