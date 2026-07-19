from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

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
    AdminBundleForm,
    AdminProductForm,
    AdminSetPasswordForm,
    AdminUserCreationForm,
    AdminUserUpdateForm,
    BulkReviewModerationForm,
    BundleItemFormSet,
    ProductDeleteConfirmationForm,
    ReviewDeleteConfirmationForm,
    ReviewModerationForm,
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
            "review_queue_count": Review.objects.filter(
                status=Review.Status.PENDING
            ).count(),
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
    product_list = Product.objects.all()
    if not request.user.is_superuser:
        product_list = product_list.exclude(product_type=Product.ProductType.BUNDLE)

    query = request.GET.get("query", "").strip()
    product_type = request.GET.get("product_type", "").strip()
    visibility = request.GET.get("visibility", "").strip()
    genre = request.GET.get("genre", "").strip()
    sort = request.GET.get("sort", "artist")
    sort_fields = {
        "artist": ("artist", "title", "product_id"),
        "-artist": ("-artist", "title", "product_id"),
        "title": ("title", "artist", "product_id"),
        "-title": ("-title", "artist", "product_id"),
        "price": ("price", "artist", "title"),
        "-price": ("-price", "artist", "title"),
    }

    if query:
        product_list = product_list.filter(
            Q(product_id__icontains=query)
            | Q(artist__icontains=query)
            | Q(title__icontains=query)
            | Q(description__icontains=query)
        )
    if product_type in Product.ProductType.values:
        product_list = product_list.filter(product_type=product_type)
    if visibility == "visible":
        product_list = product_list.filter(is_visible=True)
    elif visibility == "hidden":
        product_list = product_list.filter(is_visible=False)
    if genre:
        product_list = product_list.filter(genre=genre)

    genres = list(
        Product.objects.exclude(genre="")
        .order_by("genre")
        .values_list("genre", flat=True)
        .distinct()
    )
    page = Paginator(
        product_list.order_by(*sort_fields.get(sort, sort_fields["artist"])),
        25,
    ).get_page(request.GET.get("page"))

    return render(
        request,
        "admin_panel/product_list.html",
        {
            "active_section": "products",
            "product_page": page,
            "query": query,
            "selected_product_type": product_type,
            "selected_visibility": visibility,
            "selected_genre": genre,
            "selected_sort": sort,
            "product_types": Product.ProductType.choices,
            "genres": genres,
        },
    )


@admin_only_required
def product_create(request):
    form = AdminProductForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            product = form.save()
            record_admin_activity(
                actor=request.user,
                action=AdminActivity.Action.CREATE,
                target_type="Product",
                target_identifier=product.product_id,
                target_label=str(product),
                summary=f"Created product {product.product_id}.",
                metadata={"category": product.product_type},
            )
        messages.success(request, f"Product {product.product_id} has been created.")
        return redirect("admin_panel:product_edit", product_id=product.product_id)

    return render(
        request,
        "admin_panel/product_form.html",
        {
            "active_section": "products",
            "form": form,
            "form_title": "Add product",
            "form_description": "Create an LP, CD, or merchandise product. Use the bundle builder for bundles.",
            "submit_label": "Create product",
        },
    )


@product_editor_required
def product_edit(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    if product.product_type == Product.ProductType.BUNDLE:
        if not request.user.is_superuser:
            raise PermissionDenied("Editors cannot manage bundles.")
        return redirect("admin_panel:bundle_edit", product_id=product.product_id)

    form = AdminProductForm(
        request.POST or None,
        request.FILES or None,
        instance=product,
        allow_bundle=product.product_type == Product.ProductType.BUNDLE,
    )
    if request.method == "POST" and form.is_valid():
        changed_fields = list(form.changed_data)
        with transaction.atomic():
            product = form.save()
            record_admin_activity(
                actor=request.user,
                action=AdminActivity.Action.UPDATE,
                target_type="Product",
                target_identifier=product.product_id,
                target_label=str(product),
                summary=f"Updated product {product.product_id}.",
                metadata={"changed_fields": changed_fields},
            )
        messages.success(request, f"Product {product.product_id} has been updated.")
        return redirect("admin_panel:product_edit", product_id=product.product_id)

    return render(
        request,
        "admin_panel/product_form.html",
        {
            "active_section": "products",
            "form": form,
            "product": product,
            "form_title": f"Edit {product.title}",
            "form_description": f"Update {product.product_id} without changing its immutable product ID.",
            "submit_label": "Save product",
        },
    )


@product_editor_required
@require_POST
def product_visibility(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    if product.product_type == Product.ProductType.BUNDLE and not request.user.is_superuser:
        raise PermissionDenied("Editors cannot manage bundles.")

    action = request.POST.get("action")
    if action not in {"hide", "show"}:
        raise PermissionDenied("Unknown visibility action.")
    product.is_visible = action == "show"
    product.save(update_fields=("is_visible",))
    action_word = "Showed" if product.is_visible else "Hid"
    record_admin_activity(
        actor=request.user,
        action=AdminActivity.Action.VISIBILITY,
        target_type="Product",
        target_identifier=product.product_id,
        target_label=str(product),
        summary=f"{action_word} product {product.product_id}.",
        metadata={"is_visible": product.is_visible},
    )
    messages.success(
        request,
        f"Product {product.product_id} is now {'visible' if product.is_visible else 'hidden'}.",
    )
    next_url = request.POST.get("next", "")
    if url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect("admin_panel:products")


def _remove_product_file(product):
    if product.uploaded_image:
        product.uploaded_image.delete(save=False)


@admin_only_required
def product_delete(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    related_bundles = list(
        Product.objects.filter(bundle_items__component=product).order_by("title")
    )
    form = ProductDeleteConfirmationForm(
        request.POST or None,
        product=product,
        has_related_bundles=bool(related_bundles),
    )
    if request.method == "POST" and form.is_valid():
        delete_related = form.cleaned_data.get("delete_related_bundles", False)
        if related_bundles and not delete_related:
            form.add_error(
                None,
                "This product belongs to one or more bundles. Delete those bundles with it or cancel.",
            )
        else:
            product_identifier = product.product_id
            product_label = str(product)
            deleted_bundle_ids = [bundle.product_id for bundle in related_bundles]
            with transaction.atomic():
                for bundle in related_bundles:
                    _remove_product_file(bundle)
                    bundle.delete()
                _remove_product_file(product)
                product.delete()
                record_admin_activity(
                    actor=request.user,
                    action=AdminActivity.Action.DELETE,
                    target_type="Product",
                    target_identifier=product_identifier,
                    target_label=product_label,
                    summary=f"Permanently deleted product {product_identifier}.",
                    metadata={"deleted_bundle_ids": deleted_bundle_ids},
                )
            messages.success(
                request,
                f"Product {product_identifier} has been permanently deleted.",
            )
            return redirect("admin_panel:products")

    return render(
        request,
        "admin_panel/product_confirm_delete.html",
        {
            "active_section": "products",
            "form": form,
            "product": product,
            "related_bundles": related_bundles,
            "review_count": product.reviews.count(),
        },
    )


@admin_only_required
def bundles(request):
    bundle_list = Product.objects.filter(product_type=Product.ProductType.BUNDLE).annotate(
        component_count=Count("bundle_items"),
        total_units=Sum("bundle_items__quantity"),
    )
    query = request.GET.get("query", "").strip()
    visibility = request.GET.get("visibility", "").strip()
    if query:
        bundle_list = bundle_list.filter(
            Q(product_id__icontains=query)
            | Q(title__icontains=query)
            | Q(description__icontains=query)
        )
    if visibility == "visible":
        bundle_list = bundle_list.filter(is_visible=True)
    elif visibility == "hidden":
        bundle_list = bundle_list.filter(is_visible=False)

    page = Paginator(
        bundle_list.order_by("title", "product_id"),
        25,
    ).get_page(request.GET.get("page"))

    return render(
        request,
        "admin_panel/bundle_list.html",
        {
            "active_section": "bundles",
            "bundle_page": page,
            "query": query,
            "selected_visibility": visibility,
        },
    )


@admin_only_required
def bundle_create(request):
    bundle = Product(product_type=Product.ProductType.BUNDLE)
    form = AdminBundleForm(
        request.POST or None,
        request.FILES or None,
        instance=bundle,
    )
    formset = BundleItemFormSet(
        request.POST or None,
        instance=bundle,
        prefix="components",
    )
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            bundle = form.save()
            formset.instance = bundle
            formset.save()
            component_ids = list(
                bundle.bundle_items.order_by("position").values_list(
                    "component_id",
                    flat=True,
                )
            )
            record_admin_activity(
                actor=request.user,
                action=AdminActivity.Action.CREATE,
                target_type="Bundle",
                target_identifier=bundle.product_id,
                target_label=bundle.title,
                summary=f"Created bundle {bundle.product_id}.",
                metadata={"component_ids": component_ids},
            )
        messages.success(request, f"Bundle {bundle.product_id} has been created.")
        return redirect("admin_panel:bundle_edit", product_id=bundle.product_id)

    return render(
        request,
        "admin_panel/bundle_form.html",
        {
            "active_section": "bundles",
            "form": form,
            "formset": formset,
            "form_title": "Create bundle",
            "form_description": "Create a product from existing LPs, CDs, and merchandise.",
            "submit_label": "Create bundle",
        },
    )


@admin_only_required
def bundle_edit(request, product_id):
    bundle = get_object_or_404(
        Product,
        product_id=product_id,
        product_type=Product.ProductType.BUNDLE,
    )
    form = AdminBundleForm(
        request.POST or None,
        request.FILES or None,
        instance=bundle,
    )
    formset = BundleItemFormSet(
        request.POST or None,
        instance=bundle,
        prefix="components",
    )
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        changed_fields = list(form.changed_data)
        with transaction.atomic():
            bundle = form.save()
            formset.save()
            component_ids = list(
                bundle.bundle_items.order_by("position").values_list(
                    "component_id",
                    flat=True,
                )
            )
            record_admin_activity(
                actor=request.user,
                action=AdminActivity.Action.UPDATE,
                target_type="Bundle",
                target_identifier=bundle.product_id,
                target_label=bundle.title,
                summary=f"Updated bundle {bundle.product_id}.",
                metadata={
                    "changed_fields": changed_fields,
                    "component_ids": component_ids,
                },
            )
        messages.success(request, f"Bundle {bundle.product_id} has been updated.")
        return redirect("admin_panel:bundle_edit", product_id=bundle.product_id)

    return render(
        request,
        "admin_panel/bundle_form.html",
        {
            "active_section": "bundles",
            "form": form,
            "formset": formset,
            "bundle": bundle,
            "form_title": f"Edit {bundle.title}",
            "form_description": "Update bundle details, price, visibility, and ordered components.",
            "submit_label": "Save bundle",
        },
    )


@review_moderator_required
def reviews(request):
    review_list = Review.objects.select_related("product", "author")
    query = request.GET.get("query", "").strip()
    status = request.GET.get("status", Review.Status.PENDING).strip()
    rating = request.GET.get("rating", "").strip()
    sort = request.GET.get("sort", "-updated")
    sort_fields = {
        "-updated": ("-updated_at", "-pk"),
        "updated": ("updated_at", "pk"),
        "-created": ("-created_at", "-pk"),
        "rating": ("rating", "pk"),
        "-rating": ("-rating", "pk"),
    }

    if query:
        review_list = review_list.filter(
            Q(author__username__icontains=query)
            | Q(product__product_id__icontains=query)
            | Q(product__artist__icontains=query)
            | Q(product__title__icontains=query)
            | Q(comment__icontains=query)
        )
    if status in Review.Status.values:
        review_list = review_list.filter(status=status)
    if rating in {"1", "2", "3", "4", "5"}:
        review_list = review_list.filter(rating=int(rating))

    page = Paginator(
        review_list.order_by(*sort_fields.get(sort, sort_fields["-updated"])),
        25,
    ).get_page(request.GET.get("page"))

    return render(
        request,
        "admin_panel/review_list.html",
        {
            "active_section": "reviews",
            "review_page": page,
            "query": query,
            "selected_status": status,
            "selected_rating": rating,
            "selected_sort": sort,
            "review_statuses": Review.Status.choices,
        },
    )


@review_moderator_required
def review_detail(request, review_id):
    review = get_object_or_404(
        Review.objects.select_related("product", "author"),
        pk=review_id,
    )
    previous_status = review.status
    form = ReviewModerationForm(request.POST or None, instance=review)
    if request.method == "POST" and form.is_valid():
        review = form.save()
        record_admin_activity(
            actor=request.user,
            action=AdminActivity.Action.MODERATION,
            target_type="Review",
            target_identifier=review.pk,
            target_label=f"Review #{review.pk} by {review.author.username}",
            summary=f"Set review #{review.pk} to {review.get_status_display().lower()}.",
            metadata={
                "previous_status": previous_status,
                "new_status": review.status,
                "product_id": review.product_id,
            },
        )
        messages.success(
            request,
            f"Review #{review.pk} is now {review.get_status_display().lower()}.",
        )
        return redirect("admin_panel:review_detail", review_id=review.pk)

    return render(
        request,
        "admin_panel/review_detail.html",
        {
            "active_section": "reviews",
            "review": review,
            "form": form,
        },
    )


@review_moderator_required
@require_POST
def review_bulk_moderate(request):
    form = BulkReviewModerationForm(
        request.POST,
        queryset=Review.objects.select_related("product", "author"),
    )
    if not form.is_valid():
        messages.error(
            request,
            "Select at least one review and a valid moderation action.",
        )
        return redirect("admin_panel:reviews")

    selected_reviews = list(form.cleaned_data["selected_reviews"])
    new_status = form.cleaned_data["action"]
    rejection_reason = form.cleaned_data["rejection_reason"]
    with transaction.atomic():
        for review in selected_reviews:
            previous_status = review.status
            review.status = new_status
            review.rejection_reason = rejection_reason
            review.save(update_fields=("status", "rejection_reason", "updated_at"))
            record_admin_activity(
                actor=request.user,
                action=AdminActivity.Action.MODERATION,
                target_type="Review",
                target_identifier=review.pk,
                target_label=f"Review #{review.pk} by {review.author.username}",
                summary=f"Set review #{review.pk} to {review.get_status_display().lower()}.",
                metadata={
                    "previous_status": previous_status,
                    "new_status": review.status,
                    "product_id": review.product_id,
                    "bulk": True,
                },
            )

    messages.success(
        request,
        f"{len(selected_reviews)} review{'' if len(selected_reviews) == 1 else 's'} marked {Review.Status(new_status).label.lower()}.",
    )
    return redirect("admin_panel:reviews")


@admin_only_required
def review_delete(request, review_id):
    review = get_object_or_404(
        Review.objects.select_related("product", "author"),
        pk=review_id,
    )
    form = ReviewDeleteConfirmationForm(request.POST or None, review=review)
    if request.method == "POST" and form.is_valid():
        identifier = review.pk
        author = review.author.username
        product_id = review.product_id
        review.delete()
        record_admin_activity(
            actor=request.user,
            action=AdminActivity.Action.DELETE,
            target_type="Review",
            target_identifier=identifier,
            target_label=f"Review #{identifier} by {author}",
            summary=f"Permanently deleted review #{identifier}.",
            metadata={"author": author, "product_id": product_id},
        )
        messages.success(request, f"Review #{identifier} has been permanently deleted.")
        return redirect("admin_panel:reviews")

    return render(
        request,
        "admin_panel/review_confirm_delete.html",
        {
            "active_section": "reviews",
            "review": review,
            "form": form,
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
