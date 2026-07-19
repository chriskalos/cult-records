from django import forms

from .cart import MAX_ITEM_QUANTITY


class CartQuantityForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        max_value=MAX_ITEM_QUANTITY,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "inputmode": "numeric",
            }
        ),
    )
