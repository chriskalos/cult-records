from decimal import Decimal

from django.shortcuts import render


def home(request):
    products = [
        {
            "image": None,
            "title": "Madeon - Victory LP",
            "description": "Placeholder description for Madeon - Victory LP",
            "price": Decimal("69.99"),
        },
        {
            "image": None,
            "title": "Madonna - Confessions II LP",
            "description": "Placeholder",
            "price": Decimal("69.99"),
        },
        {
            "image": None,
            "title": "Porter Robinson - Smile LP",
            "description": "Placeholder",
            "price": Decimal("49.99"),
        },
        {
            "image": None,
            "title": "Secret Unreleased Daft Punk LP",
            "description": "Aliens",
            "price": Decimal("420.00"),
        },
    ]

    return render(request, "home/index.html", {"products": products})
