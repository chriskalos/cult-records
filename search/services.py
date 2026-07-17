import re
import unicodedata

from django.db.models import Q
from rapidfuzz import fuzz

from home.models import Product

MINIMUM_RELEVANCE = 70


def normalize_search_text(value):
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return re.sub(r"[^\w]+", " ", without_accents).strip()


def _average_token_score(query, candidate):
    query_tokens = query.split()
    candidate_tokens = candidate.split()

    if not query_tokens or not candidate_tokens:
        return 0

    token_scores = [
        max(fuzz.ratio(query_token, candidate_token) for candidate_token in candidate_tokens)
        for query_token in query_tokens
    ]
    return sum(token_scores) / len(token_scores)


def _text_score(query, candidate):
    if query in candidate:
        return 100

    return max(
        fuzz.WRatio(query, candidate),
        fuzz.token_set_ratio(query, candidate),
        _average_token_score(query, candidate),
    )


def _product_relevance(product, query):
    primary_text = normalize_search_text(f"{product.artist} {product.title}")
    description = normalize_search_text(product.description)
    complete_text = f"{primary_text} {description}"

    return max(
        _text_score(query, primary_text),
        _text_score(query, complete_text) * 0.9,
        _text_score(query, description) * 0.75,
    )


def search_products(criteria):
    products = Product.objects.public()

    if artist := criteria.get("artist"):
        products = products.filter(artist=artist)

    if genre := criteria.get("genre"):
        products = products.filter(genre=genre)

    if product_type := criteria.get("product_type"):
        products = products.filter(product_type=product_type)

    if (min_price := criteria.get("min_price")) is not None:
        products = products.filter(price__gte=min_price)

    if (max_price := criteria.get("max_price")) is not None:
        products = products.filter(price__lte=max_price)

    query = normalize_search_text(criteria.get("query", ""))

    if not query:
        return list(products.order_by("artist", "title"))

    if len(query) < 3:
        return list(
            products.filter(
                Q(title__icontains=query)
                | Q(artist__icontains=query)
                | Q(description__icontains=query)
            ).order_by("artist", "title")
        )

    ranked_products = [
        (_product_relevance(product, query), product) for product in products
    ]
    relevant_products = [
        (score, product)
        for score, product in ranked_products
        if score >= MINIMUM_RELEVANCE
    ]
    relevant_products.sort(
        key=lambda result: (
            -result[0],
            result[1].artist.casefold(),
            result[1].title.casefold(),
            result[1].product_id,
        )
    )
    return [product for _, product in relevant_products]
