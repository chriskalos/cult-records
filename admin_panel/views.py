from django.contrib.auth import get_user_model
from django.shortcuts import render

from home.models import Product
from product_page.models import Review

from .access import (
    admin_only_required,
    admin_panel_access_required,
    product_editor_required,
    review_moderator_required,
)


@admin_panel_access_required
def dashboard(request):
    User = get_user_model()
    return render(
        request,
        "admin_panel/dashboard.html",
        {
            "active_section": "dashboard",
            "total_users": User.objects.count(),
            "active_users": User.objects.filter(is_active=True).count(),
            "total_products": Product.objects.count(),
            "review_queue_count": Review.objects.filter(is_approved=False).count(),
            "recent_products": Product.objects.order_by("-product_id")[:5],
            "recent_users": User.objects.order_by("-date_joined", "-pk")[:5],
        },
    )


@admin_only_required
def users(request):
    return render(
        request,
        "admin_panel/section_placeholder.html",
        {
            "active_section": "users",
            "section_title": "Users",
            "section_description": "User accounts, roles, passwords, and deletion controls will live here.",
        },
    )


@product_editor_required
def products(request):
    return render(
        request,
        "admin_panel/section_placeholder.html",
        {
            "active_section": "products",
            "section_title": "Products",
            "section_description": "Catalogue editing and product visibility controls will live here.",
        },
    )


@admin_only_required
def bundles(request):
    return render(
        request,
        "admin_panel/section_placeholder.html",
        {
            "active_section": "bundles",
            "section_title": "Bundles",
            "section_description": "Bundle composition, quantities, ordering, and deletion controls will live here.",
        },
    )


@review_moderator_required
def reviews(request):
    return render(
        request,
        "admin_panel/section_placeholder.html",
        {
            "active_section": "reviews",
            "section_title": "Reviews",
            "section_description": "The pending, approved, and rejected moderation queues will live here.",
        },
    )


@admin_panel_access_required
def activity(request):
    return render(
        request,
        "admin_panel/section_placeholder.html",
        {
            "active_section": "activity",
            "section_title": "Activity",
            "section_description": "Administrative changes and moderation decisions will be recorded here.",
        },
    )


@admin_panel_access_required
def visuals(request):
    return render(
        request,
        "admin_panel/component_gallery.html",
        {"active_section": "visuals"},
    )
