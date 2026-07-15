from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from home.models import Product

from .forms import ReviewForm
from .models import ProductPage, Review


def _detail_context(request, product, review_form=None, is_editing_review=False):
    try:
        page = product.page
    except ProductPage.DoesNotExist:
        page = None

    long_description = (
        page.long_description if page and page.long_description else product.description
    )

    approved_reviews = product.reviews.filter(is_approved=True).select_related("author")
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
    }


def product_detail(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)

    return render(
        request,
        "product_page/detail.html",
        _detail_context(
            request,
            product,
            is_editing_review=request.GET.get("edit_review") == "1",
        ),
    )


@login_required
@require_POST
def create_review(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)

    if Review.objects.filter(product=product, author=request.user).exists():
        return redirect("product_page:detail", product_id=product.product_id)

    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.author = request.user
        review.save()
        return redirect(f"{product.get_absolute_url()}#your-review")

    return render(
        request,
        "product_page/detail.html",
        _detail_context(request, product, review_form=form),
    )


@login_required
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
        form.save()
        return redirect(f"{product.get_absolute_url()}#your-review")

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


@login_required
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
    return redirect(f"{product.get_absolute_url()}#reviews")
