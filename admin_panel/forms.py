from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.password_validation import validate_password

from accounts.roles import UserRole, role_for_user, set_user_role


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
