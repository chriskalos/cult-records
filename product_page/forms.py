from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        choices=[(rating, f"{rating} star{'s' if rating != 1 else ''}") for rating in range(1, 6)],
        coerce=int,
        widget=forms.RadioSelect(attrs={"class": "review-rating__input"}),
    )
    comment = forms.CharField(
        required=False,
        max_length=2000,
        strip=True,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "maxlength": 2000,
                "rows": 4,
            }
        ),
    )

    class Meta:
        model = Review
        fields = ("rating", "comment")
