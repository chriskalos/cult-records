# Cult Records

Cult Records is a Django web application for browsing and managing a record catalogue.

## Current functionality

The home page uses a reusable Bootstrap layout with shared header and footer templates. It displays a responsive product list populated from database records.

Public users can search the catalogue from the site header or the search page. Search terms are matched against product titles, artists, and descriptions, with relevant results ranked first. The search allows reasonable misspellings and words that appear across more than one product field.

Search results can be filtered by artist, product type, minimum price, and maximum price. The filters appear in a left sidebar on larger screens and stack above the results on smaller screens.

The product database model stores an optional image URL, artist, title, description, product type, and price. Product types are limited to LP, CD, bundle, and merch.

Each product uses a manually assigned uppercase alphanumeric product ID as its primary key.

An initial data migration adds four placeholder products for development.

## Run locally

```bash
uv run python manage.py runserver
```
