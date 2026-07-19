from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cart.models import Order

from .forms import LoginForm, RegistrationForm, UsernameUpdateForm
from .roles import role_for_user


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome to Cult Records, {user.username}.")
        return redirect("accounts:dashboard")

    return render(request, "accounts/register.html", {"form": form})


class AccountLoginView(LoginView):
    authentication_form = LoginForm
    redirect_authenticated_user = True
    template_name = "accounts/login.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Welcome back, {form.get_user().username}.")
        return response


@login_required
@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "You have signed out.")
    return redirect("home")


@login_required
def dashboard(request):
    reviews = request.user.product_reviews.select_related("product").order_by(
        "-updated_at",
        "-pk",
    )[:10]
    purchases = (
        request.user.orders.filter(status=Order.Status.PAID)
        .prefetch_related("items__product")
        .order_by("-paid_at", "-created_at")
    )
    return render(
        request,
        "accounts/dashboard.html",
        {
            "account_role": role_for_user(request.user),
            "purchases": purchases,
            "reviews": reviews,
        },
    )


@login_required
@require_POST
def mark_order_delivered(request, order_id):
    order = get_object_or_404(
        Order,
        pk=order_id,
        user=request.user,
        status=Order.Status.PAID,
    )
    order.delete()
    messages.success(
        request,
        "Order marked as delivered and removed from your dashboard.",
    )
    return redirect("accounts:dashboard")


@login_required
def edit_profile(request):
    form = UsernameUpdateForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("accounts:dashboard")

    return render(request, "accounts/edit_profile.html", {"form": form})
