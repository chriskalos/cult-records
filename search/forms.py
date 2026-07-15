from decimal import Decimal

from django import forms
from django.core.validators import MaxValueValidator
from django.db.models import Max

from home.models import Product


class SearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        max_length=100,
        label="Search",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Search by title, artist, or description",
            }
        ),
    )
    artist = forms.ChoiceField(
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select", "data-live-filter": "immediate"}
        ),
    )
    product_type = forms.ChoiceField(
        required=False,
        choices=[("", "All product types"), *Product.ProductType.choices],
        widget=forms.Select(
            attrs={"class": "form-select", "data-live-filter": "immediate"}
        ),
    )
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        label="Minimum price",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "data-live-filter": "debounced",
                "placeholder": "0.00",
            }
        ),
    )
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        label="Maximum price",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "data-live-filter": "debounced",
                "placeholder": "0.00",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        catalogue_max_price = (
            Product.objects.aggregate(max_price=Max("price"))["max_price"]
            or Decimal("0.00")
        ).quantize(Decimal("0.01"))
        data = args[0] if args else kwargs.get("data")

        if data is not None:
            data = data.copy()
            data.setdefault("min_price", "0.00")
            data.setdefault("max_price", str(catalogue_max_price))

            if args:
                args = (data, *args[1:])
            else:
                kwargs["data"] = data

        super().__init__(*args, **kwargs)
        self.catalogue_max_price = catalogue_max_price
        self.fields["min_price"].initial = Decimal("0.00")
        self.fields["max_price"].initial = catalogue_max_price

        for field_name in ("min_price", "max_price"):
            field = self.fields[field_name]
            field.max_value = catalogue_max_price
            field.validators.append(MaxValueValidator(catalogue_max_price))
            field.widget.attrs["max"] = str(catalogue_max_price)

        artists = (
            Product.objects.order_by("artist")
            .values_list("artist", flat=True)
            .distinct()
        )
        self.fields["artist"].choices = [
            ("", "All artists"),
            *((artist, artist) for artist in artists),
        ]

    def clean(self):
        cleaned_data = super().clean()
        min_price = cleaned_data.get("min_price")
        max_price = cleaned_data.get("max_price")

        if min_price is not None and max_price is not None and min_price > max_price:
            self.add_error(
                "max_price",
                "Maximum price must be greater than or equal to minimum price.",
            )

        return cleaned_data
