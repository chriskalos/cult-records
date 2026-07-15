from django import forms

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
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    product_type = forms.ChoiceField(
        required=False,
        choices=[("", "All product types"), *Product.ProductType.choices],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        label="Minimum price",
        widget=forms.NumberInput(
            attrs={"class": "form-control", "placeholder": "0.00"}
        ),
    )
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        label="Maximum price",
        widget=forms.NumberInput(
            attrs={"class": "form-control", "placeholder": "0.00"}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
