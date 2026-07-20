# Cult Records

Cult Records is a responsive record catalogue and sandbox storefront built with Django. Visitors can search and filter products, create an account, write reviews, use a shopping cart, and complete test purchases through Stripe.

**Live site:** [cult.chriskalos.xyz](https://cult.chriskalos.xyz/)

## What the website does

- Displays a catalogue of CDs, LPs, merchandise, and bundles with dedicated product pages, artwork, release information, track lists, and prices.
- Searches titles, artists, and descriptions with RapidFuzz so results tolerate reasonable misspellings. Results can also be filtered by artist, genre, format, and price.
- Lets registered users manage their username, submit one star rating and review per product, and view their review activity from an account dashboard. Reviews are published after moderation.
- Provides a session-backed shopping cart. A user can fill the cart without signing in, but must sign in before starting Stripe sandbox checkout.
- Records paid sandbox orders on the account dashboard. Users can mark an order as delivered, which removes it from their purchase history.
- Provides a custom role-protected admin panel at `/admin/` for catalogue, bundle, review, user, and activity management.
- Includes a protected Human Assets Manager, or HAM, with fictional network records and an interactive world map. An account unlocks HAM when one paid order contains exactly 42 copies of product `CLXYZCD`.

The public catalogue and admin panel use related Cult Records typography and square geometry. HAM intentionally breaks from those conventions with a Cult Radio-inspired surveillance terminal, a dried-blood palette, and an animated navbar treatment. All three interfaces retain responsive layouts and visible keyboard focus.

## Demonstration accounts

Database migrations create these accounts for local demonstration:

| Role | Username | Password |
| --- | --- | --- |
| Admin | `admin` | `admin` |
| Editor | `editor` | `editor` |
| User | `user1` to `user5` | Same as the username |

The roles provide the following access:

| Role | Access |
| --- | --- |
| Admin | Full custom admin-panel access, including users, bundles, additions, deletion, and review moderation |
| Editor | Product editing and visibility controls for non-bundle products, plus review moderation; no user, bundle, addition, or deletion access |
| User | Public catalogue, reviews, account dashboard, shopping cart, and sandbox checkout |
| Anonymous | Public catalogue, search, reviews, and shopping cart; sign-in is required for checkout and account pages |

HAM access is a separate capability from these roles. Human Asset management requires both the Admin role and HAM access.

The demonstration credentials are not for production use. Django stores their passwords as hashes rather than plain text.

## Trying the checkout

Cult Records uses Stripe's sandbox and rejects live Stripe keys. No real payment is taken, and card details are handled by Stripe's hosted Checkout page rather than the Django application.

Use Stripe's standard test card on the checkout page:

- Card number: `4242 4242 4242 4242`
- Expiry: any future date, such as `12/34`
- CVC: any three digits
- Other fields: any test values

## Technologies

| Technology | Where and why it is used |
| --- | --- |
| Python 3.13 and Django 6.0 | Application logic, routing, templates, forms, authentication, permissions, ORM queries, migrations, and tests |
| SQLite and PostgreSQL | SQLite keeps local development simple; Render PostgreSQL stores deployed application data outside the web service |
| RapidFuzz | Scores catalogue search results and supports misspelling-tolerant matching |
| Pillow | Validates uploaded catalogue artwork and HAM portraits as real image files |
| Cloudinary Python SDK and CDN | Stores production image uploads outside Render's filesystem and delivers all project images through optimized HTTPS URLs |
| HTML, CSS, and Bootstrap 5.3.3 | Provide semantic server-rendered pages, responsive layouts, reusable components, and the three visual treatments |
| Vanilla JavaScript | Handles live filters, product artwork movement, AJAX reviews, admin form interactions, and HAM map controls without a build process |
| Stripe Python library | Creates and verifies hosted sandbox Checkout Sessions and validates signed webhooks |
| Leaflet, MapLibre GL, OpenFreeMap, and OpenStreetMap | Provide HAM's interactive vector world map and geographic data |
| Gunicorn, WhiteNoise, Psycopg, and dj-database-url | Run Django on Render, serve CSS and JavaScript assets, and connect the deployed application to PostgreSQL |

Instrument Serif and Nunito Sans are loaded from Google Fonts with fallback families. Bootstrap and the map libraries are loaded from CDNs, so the project does not require npm. Python dependencies are declared in `pyproject.toml`, locked in `uv.lock`, and exported to `requirements.txt`.

## Security

- Django templates escape variable output, and the ORM avoids raw SQL interpolation.
- CSRF protection covers state-changing forms and AJAX requests.
- Server-side authentication, role, ownership, and HAM access checks protect restricted routes and actions.
- Django hashes passwords and applies its configured password validators.
- Forms and models validate prices, quantities, ratings, text lengths, image files, bundle contents, and product visibility.
- Checkout totals come from database prices. Stripe payments are accepted only after session ownership, status, amount, currency, and webhook signatures are verified.
- Uploaded files receive application-generated names. Production images are stored in Cloudinary, and the API credential is supplied through an environment variable rather than Git.

## Local setup

Cult Records requires Python 3.13 or newer. The shortest setup uses [`uv`](https://docs.astral.sh/uv/):

```bash
uv sync --locked
uv run python manage.py migrate
uv run python manage.py runserver
```

Open <http://127.0.0.1:8000/> and stop the server with `Ctrl+C`.

Local development uses Django's filesystem storage when `CLOUDINARY_URL` is not set. To exercise the production image pipeline locally, set `CLOUDINARY_URL` in the shell before starting Django. Never add that value to the repository.

To use a standard virtual environment on macOS or Linux:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

On Windows, use `py -3.13 -m venv .venv` and replace `.venv/bin/python` with `.venv\Scripts\python.exe`.

### Local Stripe checkout

Starting checkout locally requires a Stripe sandbox secret key in the `STRIPE_SECRET_KEY` environment variable. A restricted sandbox key also works when it can create and retrieve Checkout Sessions. `STRIPE_WEBHOOK_SECRET` enables signed webhook processing but is not required for the success-page verification flow.

Never add either secret to the repository.

## Tests

```bash
uv run python manage.py test
```

The standard virtual-environment Python executable can be used instead of `uv run python`.

## Deployment

`render.yaml` defines a Render web service and PostgreSQL database in the Frankfurt region. The build installs dependencies, collects static files, applies migrations, and verifies legacy media before Gunicorn starts Django. WhiteNoise serves CSS and JavaScript, while Cloudinary serves the brand logo, catalogue artwork, HAM portraits, and future admin uploads. The production service is available at [cult.chriskalos.xyz](https://cult.chriskalos.xyz/).

Render's free web service uses an ephemeral filesystem. Production image uploads do not depend on that filesystem because Django stores them directly in Cloudinary. The `CLOUDINARY_URL` secret must be added to the Render web service before deploying this version. See [DEPLOYMENT.md](DEPLOYMENT.md) for the required order and verification steps.
