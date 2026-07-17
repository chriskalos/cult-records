from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

from home.models import Product
from product_page.models import Review

from .access import (
    admin_only_required,
    admin_panel_access_required,
    product_editor_required,
    review_moderator_required,
)
from .models import AdminActivity


def _visible_activity(user):
    activity = AdminActivity.objects.select_related("actor")
    if user.is_superuser:
        return activity
    return activity.filter(actor=user)


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
            "recent_activity": _visible_activity(request.user)[:6],
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
    activity_list = _visible_activity(request.user)
    query = request.GET.get("query", "").strip()
    action = request.GET.get("action", "").strip()
    target_type = request.GET.get("target_type", "").strip()

    if query:
        activity_list = activity_list.filter(
            Q(actor__username__icontains=query)
            | Q(target_label__icontains=query)
            | Q(target_identifier__icontains=query)
            | Q(summary__icontains=query)
        )
    if action in AdminActivity.Action.values:
        activity_list = activity_list.filter(action=action)
    if target_type:
        activity_list = activity_list.filter(target_type=target_type)

    target_types = list(
        _visible_activity(request.user)
        .order_by("target_type")
        .values_list("target_type", flat=True)
        .distinct()
    )
    page = Paginator(activity_list, 25).get_page(request.GET.get("page"))

    return render(
        request,
        "admin_panel/activity_list.html",
        {
            "active_section": "activity",
            "activity_page": page,
            "activity_actions": AdminActivity.Action.choices,
            "target_types": target_types,
            "selected_action": action,
            "selected_target_type": target_type,
            "query": query,
        },
    )


@admin_panel_access_required
def visuals(request):
    return render(
        request,
        "admin_panel/component_gallery.html",
        {"active_section": "visuals"},
    )
