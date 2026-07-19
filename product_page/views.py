from functools import wraps
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import redirect_to_login
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, resolve_url
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.views.decorators.vary import vary_on_headers

from home.models import Product

from .forms import ReviewForm
from .models import ProductPage, Review


def _is_ajax_request(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _review_login_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)

        if _is_ajax_request(request):
            login_url = resolve_url(settings.LOGIN_URL)
            query = urlencode({REDIRECT_FIELD_NAME: request.get_full_path()})
            redirect_url = f"{login_url}?{query}"
            return JsonResponse({"redirect_url": redirect_url}, status=401)

        return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)

    return wrapped


def _detail_context(request, product, review_form=None, is_editing_review=False):
    try:
        page = product.page
    except ProductPage.DoesNotExist:
        page = None

    long_description = (
        page.long_description if page and page.long_description else product.description
    )

    approved_reviews = product.reviews.filter(
        status=Review.Status.APPROVED
    ).select_related("author")
    review_stats = approved_reviews.aggregate(
        average=Avg("rating"),
        count=Count("id"),
    )

    user_review = None
    if request.user.is_authenticated:
        user_review = product.reviews.filter(author=request.user).first()
        if review_form is None:
            if user_review and is_editing_review:
                review_form = ReviewForm(instance=user_review)
            elif user_review is None:
                review_form = ReviewForm()

    if user_review:
        approved_reviews = approved_reviews.exclude(pk=user_review.pk)

    bundle_items = None
    if product.product_type == Product.ProductType.BUNDLE:
        bundle_items = product.bundle_items.select_related("component").order_by(
            "position",
            "pk",
        )

    return {
        "product": product,
        "page": page,
        "long_description": long_description,
        "review_average": review_stats["average"],
        "review_count": review_stats["count"],
        "reviews": approved_reviews,
        "user_review": user_review,
        "review_form": review_form,
        "is_editing_review": is_editing_review,
        "bundle_items": bundle_items,
    }


def _review_fragment_response(
    request,
    product,
    *,
    review_form=None,
    is_editing_review=False,
    message="",
    status=200,
):
    context = _detail_context(
        request,
        product,
        review_form=review_form,
        is_editing_review=is_editing_review,
    )
    return JsonResponse(
        {
            "html": render_to_string(
                "product_page/includes/reviews_section.html",
                context,
                request=request,
            ),
            "message": message,
        },
        status=status,
    )


@vary_on_headers("X-Requested-With")
def product_detail(request, product_id):
    product = get_object_or_404(Product.objects.public(), product_id=product_id)

    is_editing_review = request.GET.get("edit_review") == "1"
    if _is_ajax_request(request):
        return _review_fragment_response(
            request,
            product,
            is_editing_review=is_editing_review,
        )

    return render(
        request,
        "product_page/detail.html",
        _detail_context(
            request,
            product,
            is_editing_review=is_editing_review,
        ),
    )


@_review_login_required
@require_POST
def create_review(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)

    if Review.objects.filter(product=product, author=request.user).exists():
        if _is_ajax_request(request):
            return _review_fragment_response(
                request,
                product,
                message="You have already reviewed this product.",
                status=409,
            )
        return redirect("product_page:detail", product_id=product.product_id)

    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.author = request.user
        review.save()
        success_message = (
            "Your review was submitted and will go live once it is approved."
        )
        if _is_ajax_request(request):
            return _review_fragment_response(
                request,
                product,
                message=success_message,
                status=201,
            )
        messages.success(request, success_message)
        return redirect(f"{product.get_absolute_url()}#your-review")

    if _is_ajax_request(request):
        return _review_fragment_response(
            request,
            product,
            review_form=form,
            status=422,
        )

    return render(
        request,
        "product_page/detail.html",
        _detail_context(request, product, review_form=form),
    )


@_review_login_required
@require_POST
def edit_review(request, product_id, review_id):
    product = get_object_or_404(Product, product_id=product_id)
    review = get_object_or_404(
        Review,
        pk=review_id,
        product=product,
        author=request.user,
    )
    form = ReviewForm(request.POST, instance=review)

    if form.is_valid():
        review = form.save(commit=False)
        review.status = Review.Status.PENDING
        review.rejection_reason = ""
        review.save()
        success_message = (
            "Your review was updated and will go live again once it is approved."
        )
        if _is_ajax_request(request):
            return _review_fragment_response(
                request,
                product,
                message=success_message,
            )
        messages.success(request, success_message)
        return redirect(f"{product.get_absolute_url()}#your-review")

    if _is_ajax_request(request):
        return _review_fragment_response(
            request,
            product,
            review_form=form,
            is_editing_review=True,
            status=422,
        )

    return render(
        request,
        "product_page/detail.html",
        _detail_context(
            request,
            product,
            review_form=form,
            is_editing_review=True,
        ),
    )


@_review_login_required
@require_POST
def delete_review(request, product_id, review_id):
    product = get_object_or_404(Product, product_id=product_id)
    review = get_object_or_404(
        Review,
        pk=review_id,
        product=product,
        author=request.user,
    )
    review.delete()
    if _is_ajax_request(request):
        return _review_fragment_response(
            request,
            product,
            message="Your review was deleted.",
        )
    return redirect(f"{product.get_absolute_url()}#reviews")
