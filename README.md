# Cult Records

Cult Records is a Django web application for browsing a record catalogue, finding products through fuzzy search and filters, and sharing product ratings and reviews. It provides account registration, authentication, profile management, role-based permissions, and a custom administrative workspace alongside a responsive catalogue interface.

## Features

### Catalogue and product pages

- A responsive catalogue presents products as CD or LP packaging with artwork, artist, title, format, description, genre, and price information.
- Every product links to a detail page with an optional release date, long description, and ordered track list.
- CD and LP artwork uses CSS-based packaging geometry and subtle pointer-driven movement. The interaction is disabled for touch input and when the browser reports a reduced-motion preference.
- Product IDs are manually assigned uppercase alphanumeric codes. LP, CD, Bundle, and Merch are controlled product categories rather than free-text values.
- Product artwork can use existing static catalogue assets or uploaded JPEG, PNG, and WebP files. Uploaded files are validated as images and limited to 8 MB.
- Hidden products are removed from the home page, search results, and direct public product URLs.
- Bundle pages list their component products, quantities, formats, and individual prices.

### Search and filtering

- Catalogue search matches titles, artists, and descriptions.
- Results are ordered by relevance and tolerate misspellings through fuzzy text matching.
- Filters cover artist, genre, product type, minimum price, and maximum price.
- Genre options are generated from catalogue data, and the price range is based on the highest catalogue price.
- Filter controls submit automatically. Price inputs use a short delay to avoid submitting while a value is being typed.

### Accounts and permissions

- Visitors can register, sign in, and sign out.
- Registration enforces case-insensitive username uniqueness and Django's configured password validation rules.
- Authenticated users have a dashboard containing their username, account role, and ten most recently updated reviews.
- Users can change their username from the protected profile page.
- The role model distinguishes Admin, Editor, User, and Anonymous access.
- Editors can access the custom admin panel to edit catalogue content and moderate reviews. They cannot add or delete products, manage bundles, manage users, or delete reviews.
- Administrators can access every admin-panel section. User management, bundle management, additions, and permanent deletion remain administrator-only responsibilities.

### Custom admin panel

- The custom panel is available at `/admin/` and does not use Django's built-in admin interface.
- Anonymous visitors are redirected to sign in, regular users receive no panel access, and every panel route applies its role check on the server.
- The dashboard shows live catalogue, visibility, account, and review-state totals; catalogue health; the pending moderation queue; recent administrative activity; and recent users for administrators.
- A reserved dashboard module defines the future simulated purchase overview without connecting payment processing.
- Role-aware navigation exposes only the sections available to the current administrator or editor.
- The responsive admin shell uses a separate dark blueprint identity with a desktop sidebar and a mobile off-canvas menu.
- `/admin/visuals/` provides the review surface for admin colors, typography, buttons, forms, badges, tables, empty states, and confirmation dialogs.
- Administrators can search, filter, add, edit, deactivate, change the fixed application role of, replace the password of, and permanently delete users. Administrators cannot change their own role, deactivate themselves, or delete themselves.
- Product management supports searching, filtering, sorting, creation, editing, image uploads, visibility changes, supplementary product-page fields, and permanent deletion. Product IDs become immutable after creation.
- Editors can edit and hide LP, CD, and merchandise products. They cannot add products, delete products, or view and manage bundle records.
- The bundle builder creates an independently priced product from ordered quantities of existing LP, CD, and merchandise products. Nested bundles are rejected in both forms and the data model.
- A component product that belongs to a bundle cannot be deleted by itself. Administrators may explicitly delete every related bundle in the same confirmed action, or cancel the deletion.
- Review moderation provides searchable pending, approved, and rejected queues, individual decisions, and bulk approval or rejection. Editors and administrators can moderate; only administrators can permanently delete reviews.
- Every successful management mutation records the actor, action, target, summary, timestamp, and relevant metadata in an audit trail. Administrators see all activity, while Editors see their own actions.
- Permanent user, product, bundle, and review deletion requires typed confirmation where an identifier is available. There is no soft-delete state.

### Ratings and reviews

- Product pages display the average rating, review count, and approved reviews in newest-first order.
- Authenticated users select a rating through an accessible five-star control and can submit one review per product with an optional comment of up to 2,000 characters.
- Review authors can edit or delete their own reviews.
- Creating, editing, and deleting a review updates the review section with AJAX. The same forms and links continue to work through normal page requests when JavaScript is unavailable.
- New and edited reviews return to pending moderation. The user receives a confirmation that the review will become public after approval.
- Rejected reviews remain visible to their author with an optional editorial reason. Editing a rejected or approved review clears its previous moderation decision and returns it to pending.
- Review deletion requires confirmation in the browser.

## Technologies

| Technology | Use in the project | Reason for use |
| --- | --- | --- |
| Python 3.13 | Application language | Provides the runtime required by the project and Django 6.0. |
| Django 6.0 | Routing, views, templates, forms, authentication, authorization, ORM, migrations, and testing | Supplies an integrated web framework with built-in security and data-management features. |
| SQLite | Development database | Keeps local setup simple while supporting Django's relational models and migrations. |
| RapidFuzz | Search relevance scoring | Provides efficient fuzzy string comparison for misspelling-tolerant catalogue search. |
| Pillow | Uploaded image validation | Lets Django verify and store real catalogue artwork uploads. |
| HTML and Django templates | Page structure and server-rendered content | Produce semantic pages while allowing shared layouts and reusable components. |
| CSS | Visual identity, responsive refinements, and CD/LP artwork presentation | Applies the Cult Records design system and packaging effects without an external 3D library. |
| Bootstrap 5.3.3 | Responsive grid, navigation, forms, cards, dropdowns, modal behavior, and utility classes | Provides an accessible responsive component baseline that is customized by the project stylesheet. |
| Vanilla JavaScript | Search filter behavior, product artwork movement, interactive star ratings, AJAX review updates, dynamic bundle rows, bulk review selection, and delete confirmation | Adds browser interactions without a JavaScript framework or build process. |

The Python project declares Django, RapidFuzz, and Pillow as direct dependencies in `pyproject.toml`. Exact direct and transitive versions are recorded in `uv.lock` and exported to `requirements.txt`. Bootstrap's CSS and JavaScript bundle are loaded from jsDelivr, so the project does not require npm.

## Visual design and accessibility

The public interface uses a fixed dark theme built around near-black, Oxblood, red, and Bone colors. The admin panel uses a separate dark blueprint palette so management work is clearly distinguished from the storefront. Instrument Serif is used for headings and Nunito Sans for body and interface text. Both open-source typefaces are loaded from Google Fonts with local fallback families.

Bootstrap supplies the responsive foundation, while the global stylesheet applies square controls, visible keyboard focus outlines, high-contrast text, and shadow-free surfaces. Layouts collapse for narrow screens, interactive artwork respects reduced-motion settings, and shared templates provide consistent navigation and footer landmarks. The `/visuals/` route provides a component gallery for typography, colors, controls, forms, tables, pagination, modal content, product cards, and the shared page chrome.

## Security

- Django's ORM builds database queries without interpolating user input into raw SQL.
- Django templates escape variable output by default.
- CSRF middleware and form tokens protect state-changing form submissions.
- Authentication middleware, `login_required` checks, and server-side ownership queries protect account and review actions.
- Custom admin-panel access checks enforce administrator and editor capabilities on every protected route.
- Admin forms expose fixed application roles instead of Django permission records. Administrators cannot remove their own Admin role or deactivate their own account.
- Passwords use Django's password hashing system and configured password validators.
- Review ratings, comment length, moderation state, product IDs, prices, image files, bundle components, quantities, ordering, and track data are validated on the server.
- Review ownership is enforced when editing or deleting, and database constraints allow only one review per user and product.
- Sign-out, visibility changes, bulk moderation, and public review mutations accept POST requests rather than GET requests.
- Uploaded filenames are generated by the application and stored below the configured media root rather than trusting a client path.

## Project structure

| Django app | Responsibility |
| --- | --- |
| `admin_panel` | Custom administration dashboard, access controls, audit trail, blueprint interface, and user, catalogue, bundle, and review workflows |
| `home` | Catalogue and bundle data, uploaded artwork, home page, shared templates, global styles, and product artwork presentation |
| `search` | Search form, catalogue filters, fuzzy relevance scoring, and filter interactions |
| `product_page` | Product details, supplementary product information, ratings, and reviews |
| `accounts` | Registration, authentication, dashboard, profile editing, roles, and seeded demonstration users |
| `visuals` | Reusable component and visual identity gallery |
| `cultrecords` | Project settings and root URL configuration |

## Demonstration accounts

Database migrations create the following accounts for local demonstration:

| Role | Username | Password |
| --- | --- | --- |
| Admin | `admin` | `admin` |
| Editor | `editor` | `editor` |
| User | `user1` | `user1` |
| User | `user2` | `user2` |
| User | `user3` | `user3` |
| User | `user4` | `user4` |
| User | `user5` | `user5` |

These credentials are for local demonstration only. Django stores the passwords as hashes rather than plain text.

## Local setup

Cult Records requires Python 3.13 or newer. It can be installed with standard Python tools or with `uv`.

### Windows with standard Python

Install Python 3.13 from the [Python website](https://www.python.org/downloads/windows/) if necessary. Open Command Prompt or PowerShell in the project folder and run:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py runserver
```

### macOS or Linux with standard Python

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

Open <http://127.0.0.1:8000/> in a browser. Stop the server with `Ctrl+C`.

### Setup with uv

Install `uv` using its [official installation guide](https://docs.astral.sh/uv/getting-started/installation/), then run:

```bash
uv sync --locked
uv run python manage.py migrate
uv run python manage.py runserver
```

`uv` creates the virtual environment and installs the versions recorded in `uv.lock`. The standard Python instructions install the same resolved dependency versions from `requirements.txt`.

## Tests

Run the Django test suite with either command:

```bash
uv run python manage.py test
```

```bash
.venv/bin/python manage.py test
```

On Windows, the equivalent standard Python command is:

```powershell
.venv\Scripts\python.exe manage.py test
```

## Dependency maintenance

When Python dependencies change, update `uv.lock` and regenerate `requirements.txt`:

```bash
uv lock
uv export --format requirements-txt --no-emit-project --no-hashes --no-annotate --output-file requirements.txt
```
