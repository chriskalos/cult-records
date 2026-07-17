from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from home.models import Product
from product_page.models import Review

from .access import (
    admin_only_required,
    admin_panel_access_required,
    product_editor_required,
    review_moderator_required,
)
from .audit import record_admin_activity
from .forms import (
    AdminSetPasswordForm,
    AdminUserCreationForm,
    AdminUserUpdateForm,
    UserDeleteConfirmationForm,
)
from .models import AdminActivity
from accounts.roles import EDITOR_GROUP_NAME, UserRole, role_for_user


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
    User = get_user_model()
    user_list = User.objects.annotate(review_count=Count("product_reviews"))
    query = request.GET.get("query", "").strip()
    role = request.GET.get("role", "").strip()
    status = request.GET.get("status", "").strip()
    sort = request.GET.get("sort", "username")
    sort_fields = {
        "username": "username",
        "-username": "-username",
        "joined": "date_joined",
        "-joined": "-date_joined",
        "last_login": "last_login",
        "-last_login": "-last_login",
    }

    if query:
        user_list = user_list.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        )
    if role == UserRole.ADMIN:
        user_list = user_list.filter(is_superuser=True)
    elif role == UserRole.EDITOR:
        user_list = user_list.filter(
            is_superuser=False,
            groups__name=EDITOR_GROUP_NAME,
        )
    elif role == UserRole.USER:
        user_list = user_list.filter(is_superuser=False).exclude(
            groups__name=EDITOR_GROUP_NAME
        )
    if status == "active":
        user_list = user_list.filter(is_active=True)
    elif status == "inactive":
        user_list = user_list.filter(is_active=False)

    user_list = user_list.distinct().order_by(sort_fields.get(sort, "username"), "pk")
    page = Paginator(user_list, 25).get_page(request.GET.get("page"))
    for managed_user in page.object_list:
        managed_user.admin_role = role_for_user(managed_user)

    return render(
        request,
        "admin_panel/user_list.html",
        {
            "active_section": "users",
            "user_page": page,
            "query": query,
            "selected_role": role,
            "selected_status": status,
            "selected_sort": sort,
            "role_choices": (
                (UserRole.ADMIN, "Admin"),
                (UserRole.EDITOR, "Editor"),
                (UserRole.USER, "User"),
            ),
        },
    )


@admin_only_required
def user_create(request):
    form = AdminUserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        role = role_for_user(user)
        record_admin_activity(
            actor=request.user,
            action=AdminActivity.Action.CREATE,
            target_type="User",
            target_identifier=user.pk,
            target_label=user.username,
            summary=f"Created user {user.username} as {role}.",
            metadata={"role": role},
        )
        messages.success(request, f"User {user.username} has been created.")
        return redirect("admin_panel:user_edit", user_id=user.pk)

    return render(
        request,
        "admin_panel/user_form.html",
        {
            "active_section": "users",
            "form": form,
            "form_title": "Add user",
            "form_description": "Create an account and assign one fixed application role.",
            "submit_label": "Create user",
        },
    )


@admin_only_required
def user_edit(request, user_id):
    user = get_object_or_404(get_user_model(), pk=user_id)
    original_role = role_for_user(user)
    form = AdminUserUpdateForm(
        request.POST or None,
        instance=user,
        actor=request.user,
    )
    if request.method == "POST" and form.is_valid():
        changed_fields = list(form.changed_data)
        user = form.save()
        new_role = role_for_user(user)
        action = (
            AdminActivity.Action.ROLE
            if new_role != original_role
            else AdminActivity.Action.UPDATE
        )
        record_admin_activity(
            actor=request.user,
            action=action,
            target_type="User",
            target_identifier=user.pk,
            target_label=user.username,
            summary=f"Updated user {user.username}.",
            metadata={
                "changed_fields": changed_fields,
                "previous_role": original_role,
                "new_role": new_role,
            },
        )
        messages.success(request, f"User {user.username} has been updated.")
        return redirect("admin_panel:user_edit", user_id=user.pk)

    return render(
        request,
        "admin_panel/user_form.html",
        {
            "active_section": "users",
            "form": form,
            "managed_user": user,
            "form_title": f"Edit {user.username}",
            "form_description": "Update account details, status, and application role.",
            "submit_label": "Save user",
        },
    )


@admin_only_required
def user_password(request, user_id):
    user = get_object_or_404(get_user_model(), pk=user_id)
    form = AdminSetPasswordForm(user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        if user == request.user:
            update_session_auth_hash(request, user)
        record_admin_activity(
            actor=request.user,
            action=AdminActivity.Action.PASSWORD,
            target_type="User",
            target_identifier=user.pk,
            target_label=user.username,
            summary=f"Changed the password for {user.username}.",
        )
        messages.success(request, f"The password for {user.username} has been changed.")
        return redirect("admin_panel:user_edit", user_id=user.pk)

    return render(
        request,
        "admin_panel/user_password.html",
        {
            "active_section": "users",
            "form": form,
            "managed_user": user,
        },
    )


@admin_only_required
def user_delete(request, user_id):
    user = get_object_or_404(get_user_model(), pk=user_id)
    if user == request.user:
        raise PermissionDenied("Administrators cannot delete their own account.")
    if user.is_superuser and user.is_active:
        other_admin_exists = get_user_model().objects.filter(
            is_superuser=True,
            is_active=True,
        ).exclude(pk=user.pk).exists()
        if not other_admin_exists:
            raise PermissionDenied("The last active administrator cannot be deleted.")

    form = UserDeleteConfirmationForm(request.POST or None, user=user)
    if request.method == "POST" and form.is_valid():
        user_id_value = user.pk
        username = user.username
        review_count = user.product_reviews.count()
        user.delete()
        record_admin_activity(
            actor=request.user,
            action=AdminActivity.Action.DELETE,
            target_type="User",
            target_identifier=user_id_value,
            target_label=username,
            summary=f"Permanently deleted user {username}.",
            metadata={"deleted_review_count": review_count},
        )
        messages.success(request, f"User {username} has been permanently deleted.")
        return redirect("admin_panel:users")

    return render(
        request,
        "admin_panel/user_confirm_delete.html",
        {
            "active_section": "users",
            "form": form,
            "managed_user": user,
            "review_count": user.product_reviews.count(),
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
