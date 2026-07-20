from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.password_validation import validate_password
from django.core.validators import MinValueValidator
from django.db import transaction
from django.forms import BaseInlineFormSet, inlineformset_factory

from accounts.roles import UserRole, role_for_user, set_user_role
from ham.models import HumanAsset
from home.models import BundleItem, Product
from product_page.models import ProductPage, Review


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
        label="Remove the uploaded image and use the existing CDN image or placeholder",
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
        instance = kwargs.get("instance")
        self._original_uploaded_image_name = (
            instance.uploaded_image.name
            if instance and instance.uploaded_image
            else ""
        )
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
            if (
                self.instance.product_type == Product.ProductType.BUNDLE
                and "product_type" in self.fields
            ):
                self.fields["product_type"].disabled = True
        if "product_type" in self.fields and not (
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
        if not image or "uploaded_image" not in self.changed_data:
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

    def clean(self):
        cleaned_data = super().clean()
        if (
            "uploaded_image" in self.changed_data
            and cleaned_data.get("uploaded_image")
            and cleaned_data.get("remove_uploaded_image")
        ):
            self.add_error(
                "remove_uploaded_image",
                "Choose a replacement image or remove the current image, not both.",
            )
        return cleaned_data

    def save(self, commit=True):
        product = super().save(commit=False)
        if self.cleaned_data.get("remove_uploaded_image"):
            product.uploaded_image = ""
        if commit:
            product.save()
            current_image_name = (
                product.uploaded_image.name if product.uploaded_image else ""
            )
            if (
                self._original_uploaded_image_name
                and self._original_uploaded_image_name != current_image_name
            ):
                storage = Product._meta.get_field("uploaded_image").storage
                transaction.on_commit(
                    lambda name=self._original_uploaded_image_name: storage.delete(name)
                )
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


class AdminHumanAssetForm(forms.ModelForm):
    asset_code = forms.RegexField(
        regex=r"^[A-Z0-9-]+$",
        max_length=20,
        help_text="Use uppercase letters, numbers, and hyphens.",
    )
    remove_uploaded_portrait = forms.BooleanField(
        required=False,
        label="Remove the uploaded portrait and use the existing CDN portrait",
    )

    class Meta:
        model = HumanAsset
        fields = (
            "asset_code",
            "name",
            "alias",
            "status",
            "location_label",
            "latitude",
            "longitude",
            "portrait",
            "uploaded_portrait",
            "network_role",
            "civilian_cover",
            "joined_on",
            "last_contact",
            "consensus",
            "exposure",
            "summary",
            "network_notes",
            "known_irregularity",
            "is_visible",
        )
        labels = {
            "portrait": "Existing CDN portrait URL",
            "uploaded_portrait": "Upload portrait",
        }
        help_texts = {
            "portrait": "Existing portraits use a secure Cloudinary delivery URL.",
            "is_visible": "Visible assets appear on the HAM map and in the dossier directory.",
        }
        widgets = {
            "asset_code": forms.TextInput(
                attrs={"autocomplete": "off", "spellcheck": "false"}
            ),
            "name": forms.TextInput(attrs={"autocomplete": "off"}),
            "alias": forms.TextInput(attrs={"autocomplete": "off"}),
            "location_label": forms.TextInput(attrs={"autocomplete": "off"}),
            "latitude": forms.NumberInput(attrs={"step": "0.000001"}),
            "longitude": forms.NumberInput(attrs={"step": "0.000001"}),
            "portrait": forms.TextInput(
                attrs={"autocomplete": "off", "spellcheck": "false"}
            ),
            "uploaded_portrait": forms.FileInput(
                attrs={"accept": "image/jpeg,image/png,image/webp"}
            ),
            "network_role": forms.TextInput(attrs={"autocomplete": "off"}),
            "civilian_cover": forms.TextInput(attrs={"autocomplete": "off"}),
            "joined_on": forms.DateInput(attrs={"type": "date"}),
            "last_contact": forms.DateInput(attrs={"type": "date"}),
            "summary": forms.Textarea(attrs={"rows": 4}),
            "network_notes": forms.Textarea(attrs={"rows": 5}),
            "known_irregularity": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")
        self._original_uploaded_portrait_name = (
            instance.uploaded_portrait.name
            if instance and instance.uploaded_portrait
            else ""
        )
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["asset_code"].disabled = True
            self.fields["asset_code"].help_text = "Asset codes are immutable."
        if not self.instance.uploaded_portrait:
            self.fields.pop("remove_uploaded_portrait")
        _apply_admin_form_classes(self)

    def clean_uploaded_portrait(self):
        image = self.cleaned_data.get("uploaded_portrait")
        if not image or "uploaded_portrait" not in self.changed_data:
            return image
        if image.size > 8 * 1024 * 1024:
            raise forms.ValidationError("Upload an image no larger than 8 MB.")
        image_format = getattr(getattr(image, "image", None), "format", "")
        if image_format not in {"JPEG", "PNG", "WEBP"}:
            raise forms.ValidationError("Upload a JPEG, PNG, or WebP image.")
        return image

    def clean(self):
        cleaned_data = super().clean()
        uploaded_changed = (
            "uploaded_portrait" in self.changed_data
            and cleaned_data.get("uploaded_portrait")
        )
        remove_uploaded = cleaned_data.get("remove_uploaded_portrait")
        if uploaded_changed and remove_uploaded:
            self.add_error(
                "remove_uploaded_portrait",
                "Choose a replacement portrait or remove the current portrait, not both.",
            )

        has_uploaded_portrait = bool(
            uploaded_changed
            or (self.instance.uploaded_portrait and not remove_uploaded)
        )
        if not cleaned_data.get("portrait") and not has_uploaded_portrait:
            self.add_error(
                "uploaded_portrait",
                "Provide an uploaded portrait or a stored static portrait path.",
            )

        joined_on = cleaned_data.get("joined_on")
        last_contact = cleaned_data.get("last_contact")
        if joined_on and last_contact and last_contact < joined_on:
            self.add_error(
                "last_contact",
                "Last contact cannot be earlier than the connected date.",
            )
        return cleaned_data

    def save(self, commit=True):
        asset = super().save(commit=False)
        if self.cleaned_data.get("remove_uploaded_portrait"):
            asset.uploaded_portrait = ""
        if commit:
            asset.save()
            current_portrait_name = (
                asset.uploaded_portrait.name if asset.uploaded_portrait else ""
            )
            if (
                self._original_uploaded_portrait_name
                and self._original_uploaded_portrait_name != current_portrait_name
            ):
                storage = HumanAsset._meta.get_field("uploaded_portrait").storage
                transaction.on_commit(
                    lambda name=self._original_uploaded_portrait_name: storage.delete(
                        name
                    )
                )
        return asset


class HumanAssetDeleteConfirmationForm(forms.Form):
    confirm_asset_code = forms.CharField(
        label="Type the asset code to confirm",
        widget=forms.TextInput(attrs={"autocomplete": "off", "class": "form-control"}),
    )

    def __init__(self, *args, asset, **kwargs):
        self.asset = asset
        super().__init__(*args, **kwargs)

    def clean_confirm_asset_code(self):
        asset_code = self.cleaned_data["confirm_asset_code"].strip()
        if asset_code != self.asset.asset_code:
            raise forms.ValidationError("The asset code does not match.")
        return asset_code


class AdminBundleForm(AdminProductForm):
    class Meta(AdminProductForm.Meta):
        fields = tuple(
            field
            for field in AdminProductForm.Meta.fields
            if field != "product_type"
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, allow_bundle=True, **kwargs)
        self.fields.pop("product_type", None)
        if not self.instance.pk:
            self.fields["artist"].initial = "Cult Records"

    def save(self, commit=True):
        self.instance.product_type = Product.ProductType.BUNDLE
        return super().save(commit=commit)


class BundleItemForm(forms.ModelForm):
    class Meta:
        model = BundleItem
        fields = ("component", "quantity", "position")
        widgets = {
            "quantity": forms.NumberInput(attrs={"min": 1}),
            "position": forms.NumberInput(attrs={"min": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["component"].queryset = Product.objects.exclude(
            product_type=Product.ProductType.BUNDLE
        ).order_by("artist", "title", "product_type")
        _apply_admin_form_classes(self)


class BaseBundleItemFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        components = []
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or form.cleaned_data.get("DELETE"):
                continue
            component = form.cleaned_data.get("component")
            if component:
                components.append(component.pk)

        if not components:
            raise forms.ValidationError("A bundle must contain at least one product.")
        if len(components) != len(set(components)):
            raise forms.ValidationError("A product can only appear once in a bundle.")


BundleItemFormSet = inlineformset_factory(
    Product,
    BundleItem,
    fk_name="bundle",
    form=BundleItemForm,
    formset=BaseBundleItemFormSet,
    fields=("component", "quantity", "position"),
    extra=1,
    can_delete=True,
)


class ReviewModerationForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("status", "rejection_reason")
        widgets = {
            "rejection_reason": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Optional feedback shown to the reviewer",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_admin_form_classes(self)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("status") != Review.Status.REJECTED:
            cleaned_data["rejection_reason"] = ""
        return cleaned_data


class BulkReviewModerationForm(forms.Form):
    selected_reviews = forms.ModelMultipleChoiceField(
        queryset=Review.objects.none(),
    )
    action = forms.ChoiceField(
        choices=(
            (Review.Status.APPROVED, "Approve selected"),
            (Review.Status.REJECTED, "Reject selected"),
        )
    )
    rejection_reason = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["selected_reviews"].queryset = (
            queryset if queryset is not None else Review.objects.all()
        )
        _apply_admin_form_classes(self)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("action") != Review.Status.REJECTED:
            cleaned_data["rejection_reason"] = ""
        return cleaned_data


class ReviewDeleteConfirmationForm(forms.Form):
    confirm_review_id = forms.CharField(
        label="Type the review ID to confirm",
        widget=forms.TextInput(attrs={"autocomplete": "off", "class": "form-control"}),
    )

    def __init__(self, *args, review, **kwargs):
        self.review = review
        super().__init__(*args, **kwargs)

    def clean_confirm_review_id(self):
        review_id = self.cleaned_data["confirm_review_id"].strip()
        if review_id != str(self.review.pk):
            raise forms.ValidationError("The review ID does not match.")
        return review_id
