# Cult Records

Cult Records is a Django web application for browsing and managing a record catalogue.

## Current functionality

The home page uses a reusable Bootstrap layout with shared header and footer templates. It displays a responsive product list populated from database records.

The product database model stores an optional image URL, artist, title, description, product type, and price. Product types are limited to LP, CD, bundle, and merch.

Each product uses a manually assigned uppercase alphanumeric product ID as its primary key.

An initial data migration adds four placeholder products for development.

## Run locally

```bash
uv run python manage.py runserver
```
