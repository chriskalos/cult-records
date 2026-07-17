from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.password_validation import validate_password
from django.core.validators import MinValueValidator

from accounts.roles import UserRole, role_for_user, set_user_role
from home.models import Product
from product_page.models import ProductPage


ROLE_CHOICES = (
    (UserRole.ADMIN, "Admin"),
    (UserRole.EDITOR, "Editor"),
    (UserRole.USER, "User"),
)


def _validate_unique_username(username, instance=None):
    duplicate = get_user_model().objects.filter(username__iexact=username)
    if instance and instance.pk:
        duplicate = duplicate.exclude(pk=instance.pk)
    if duplicate.exists():
        raise forms.ValidationError("A user with that username already exists.")
    return username


def _apply_admin_form_classes(form):
    for field in form.fields.values():
        if isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs.setdefault("class", "form-check-input")
        elif isinstance(field.widget, forms.Select):
            field.widget.attrs.setdefault("class", "form-select")
        else:
            field.widget.attrs.setdefault("class", "form-control")


class AdminUserCreationForm(forms.ModelForm):
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = get_user_model()
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
        )
        widgets = {
            "username": forms.TextInput(attrs={"autocomplete": "username"}),
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["is_active"].initial = True
        self.fields["role"].initial = UserRole.USER
        _apply_admin_form_classes(self)

    def clean_username(self):
        return _validate_unique_username(self.cleaned_data["username"].strip())

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields did not match.")
        if password2:
            candidate = get_user_model()(
                username=self.cleaned_data.get("username", ""),
                first_name=self.cleaned_data.get("first_name", ""),
                last_name=self.cleaned_data.get("last_name", ""),
                email=self.cleaned_data.get("email", ""),
            )
            validate_password(password2, candidate)
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            set_user_role(user, self.cleaned_data["role"])
        return user


class AdminUserUpdateForm(forms.ModelForm):
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = get_user_model()
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
        )
        widgets = {
            "username": forms.TextInput(attrs={"autocomplete": "username"}),
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
        }

    def __init__(self, *args, actor, **kwargs):
        self.actor = actor
        super().__init__(*args, **kwargs)
        self.original_role = role_for_user(self.instance)
        self.fields["role"].initial = self.original_role
        if self.instance == actor:
            self.fields["role"].disabled = True
            self.fields["role"].help_text = "You cannot change your own role."
        _apply_admin_form_classes(self)

    def clean_username(self):
        return _validate_unique_username(
            self.cleaned_data["username"].strip(),
            instance=self.instance,
        )

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        is_active = cleaned_data.get("is_active")

        if self.instance == self.actor and is_active is False:
            self.add_error("is_active", "You cannot deactivate your own account.")

        removing_active_admin = (
            self.instance.is_superuser
            and self.instance.is_active
            and (role != UserRole.ADMIN or is_active is False)
        )
        if removing_active_admin:
            other_admin_exists = get_user_model().objects.filter(
                is_superuser=True,
                is_active=True,
            ).exclude(pk=self.instance.pk).exists()
            if not other_admin_exists:
                self.add_error(
                    "role",
                    "The last active administrator cannot lose administrator access.",
                )
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            set_user_role(user, self.cleaned_data["role"])
        return user


class AdminSetPasswordForm(SetPasswordForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        _apply_admin_form_classes(self)


class UserDeleteConfirmationForm(forms.Form):
    confirm_username = forms.CharField(
        label="Type the username to confirm",
        widget=forms.TextInput(attrs={"autocomplete": "off", "class": "form-control"}),
    )

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_confirm_username(self):
        username = self.cleaned_data["confirm_username"]
        if username != self.user.username:
            raise forms.ValidationError("The username does not match.")
        return username


class AdminProductForm(forms.ModelForm):
    price = forms.DecimalField(
        min_value=Decimal("0.01"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    long_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 8}),
    )
    release_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    tracks = forms.CharField(
        required=False,
        help_text="Enter one track per line. The displayed order matches this list.",
        widget=forms.Textarea(attrs={"rows": 10}),
    )
    remove_uploaded_image = forms.BooleanField(
        required=False,
        label="Remove the uploaded image and use the existing static image or placeholder",
    )

    class Meta:
        model = Product
        fields = (
            "product_id",
            "uploaded_image",
            "artist",
            "title",
            "description",
            "genre",
            "product_type",
            "price",
            "is_visible",
        )
        widgets = {
            "product_id": forms.TextInput(
                attrs={"autocomplete": "off", "spellcheck": "false"}
            ),
            "uploaded_image": forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
            "artist": forms.TextInput(attrs={"autocomplete": "off"}),
            "title": forms.TextInput(attrs={"autocomplete": "off"}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "genre": forms.TextInput(attrs={"autocomplete": "off"}),
        }

    def __init__(self, *args, allow_bundle=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.allow_bundle = allow_bundle
        if self.instance and self.instance.pk:
            self.fields["product_id"].disabled = True
            self.fields["product_id"].help_text = "Product IDs are immutable."
            try:
                page = self.instance.page
            except ProductPage.DoesNotExist:
                page = None
            if page:
                self.fields["long_description"].initial = page.long_description
                self.fields["release_date"].initial = page.release_date
                self.fields["tracks"].initial = "\n".join(page.tracks)
            if self.instance.product_type == Product.ProductType.BUNDLE:
                self.fields["product_type"].disabled = True
        if not (
            self.instance
            and self.instance.pk
            and self.instance.product_type == Product.ProductType.BUNDLE
        ):
            self.fields["product_type"].choices = [
                choice
                for choice in Product.ProductType.choices
                if choice[0] != Product.ProductType.BUNDLE
            ]

        if not self.instance.uploaded_image:
            self.fields.pop("remove_uploaded_image")
        _apply_admin_form_classes(self)

    def clean_uploaded_image(self):
        image = self.cleaned_data.get("uploaded_image")
        if not image:
            return image
        if image.size > 8 * 1024 * 1024:
            raise forms.ValidationError("Upload an image no larger than 8 MB.")
        image_format = getattr(getattr(image, "image", None), "format", "")
        if image_format not in {"JPEG", "PNG", "WEBP"}:
            raise forms.ValidationError("Upload a JPEG, PNG, or WebP image.")
        return image

    def clean_tracks(self):
        value = self.cleaned_data.get("tracks", "")
        tracks = [line.strip() for line in value.splitlines() if line.strip()]
        if len(tracks) > 200:
            raise forms.ValidationError("A track list cannot contain more than 200 tracks.")
        if any(len(track) > 255 for track in tracks):
            raise forms.ValidationError("Each track name must be 255 characters or fewer.")
        return tracks

    def save(self, commit=True):
        product = super().save(commit=False)
        if self.cleaned_data.get("remove_uploaded_image") and product.uploaded_image:
            product.uploaded_image.delete(save=False)
            product.uploaded_image = ""
        if commit:
            product.save()
            page, _ = ProductPage.objects.get_or_create(product=product)
            page.long_description = self.cleaned_data["long_description"]
            page.release_date = self.cleaned_data["release_date"]
            page.tracks = self.cleaned_data["tracks"]
            page.full_clean()
            page.save()
        return product


class ProductDeleteConfirmationForm(forms.Form):
    confirm_product_id = forms.CharField(
        label="Type the product ID to confirm",
        widget=forms.TextInput(attrs={"autocomplete": "off", "class": "form-control"}),
    )
    delete_related_bundles = forms.BooleanField(
        required=False,
        label="Also permanently delete every bundle containing this product",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def __init__(self, *args, product, has_related_bundles=False, **kwargs):
        self.product = product
        super().__init__(*args, **kwargs)
        if not has_related_bundles:
            self.fields.pop("delete_related_bundles")

    def clean_confirm_product_id(self):
        product_id = self.cleaned_data["confirm_product_id"]
        if product_id != self.product.product_id:
            raise forms.ValidationError("The product ID does not match.")
        return product_id
