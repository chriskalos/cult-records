from django.shortcuts import render

from .forms import SearchForm


def search(request):
    form = SearchForm(request.GET or None)
    return render(request, "search/results.html", {"form": form})
