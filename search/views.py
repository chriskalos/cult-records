from django.shortcuts import render

from .forms import SearchForm
from .services import search_products


def search(request):
    form = SearchForm(request.GET or None)
    products = None

    if form.is_bound and form.is_valid():
        products = search_products(form.cleaned_data)

    return render(
        request,
        "search/results.html",
        {"form": form, "products": products},
    )
