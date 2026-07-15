# Cult Records

Cult Records is a Django web application for browsing and managing a record catalogue.

## Current functionality

The home page uses a reusable Bootstrap layout with shared header and footer templates. It displays a responsive product list populated from database records.

Public users can search the catalogue from the site header or the search page. Search terms are matched against product titles, artists, and descriptions, with relevant results ranked first. The search allows reasonable misspellings and words that appear across more than one product field.

Search results can be filtered by artist, genre, product type, minimum price, and maximum price. Genre filtering uses an exact-match list populated from the catalogue. Price filtering uses a dual-ended slider with editable values. Its range starts at zero and ends at the highest product price currently in the catalogue. Filters apply automatically when changed, with a short delay for price input. The filters appear in a left sidebar on larger screens and stack above the results on smaller screens.

The product database model stores an optional static image path, artist, title, short description, optional genre, product type, and price. Product types are limited to LP, CD, bundle, and merch.

Each product uses a manually assigned uppercase alphanumeric product ID as its primary key.

Every catalogue card links to a responsive product detail page. Supplementary product-page records use the product ID as a one-to-one primary key and can store a long description, an exact release date, and an ordered JSON list of track names. All supplementary fields are optional. A product without a supplementary record still has a detail page and uses its short catalogue description as a fallback.

Product pages include a reviews section with a dynamically calculated average rating and review count. Approved reviews appear newest first. Authenticated users can submit one review per product with a rating from one to five and an optional comment of up to 2,000 characters. They can later edit or delete their own review. Anonymous visitors see an inactive review form with a link to sign in.

Visitors can register with a username and password, sign in, and sign out. Registration signs the new user in automatically. Usernames must be unique regardless of capitalization, and new passwords are checked with Django's configured password validators. Password changes are handled by an administrator because the application does not collect email addresses.

Every authenticated user has a protected dashboard showing their username, account type, and recent review activity. Users can update their own username, but cannot change their role or permissions. Signing in from a product's review section returns the user to that product.

The application recognizes Admin, Editor, User, and Anonymous roles. Admins have full permissions. Editors are assigned catalogue management and review moderation permissions, but not user-management permissions. The future custom management interface will restrict review moderation to approving, hiding, and deleting reviews rather than rewriting their content. Ordinary Users have no management permissions and can only edit or delete their own reviews. Anonymous visitors can only browse the public catalogue. Django's admin interface is not exposed because catalogue and account management will use a custom interface.

The catalogue contains 11 CD and LP products from cursed locale, Madeon, Madonna, Balu Brigada, and Rick Astley. CDs cost 6.99€ and LPs cost 14.99€. Catalogue genres use Electronic for cursed locale and Madeon, Pop for Madonna and Rick Astley, and Alternative for Balu Brigada. Album artwork is stored with the application as static image assets.

## Default development accounts

Database migrations create the following development accounts:

| Role | Username | Password |
| --- | --- | --- |
| Admin | `admin` | `admin` |
| Editor | `editor` | `editor` |
| User | `user1` | `user1` |
| User | `user2` | `user2` |
| User | `user3` | `user3` |
| User | `user4` | `user4` |
| User | `user5` | `user5` |

These credentials are intended for local development and demonstration only. Passwords are stored as Django password hashes rather than plain text.

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
