from django import forms

from .models import LoanRequest


class LoanRequestForm(forms.ModelForm):
    class Meta:
        model = LoanRequest
        fields = ["purpose", "expected_start_date", "expected_return_date", "notes"]
        widgets = {
            "expected_start_date": forms.DateInput(attrs={"type": "date"}),
            "expected_return_date": forms.DateInput(attrs={"type": "date"}),
            "purpose": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }
        labels = {
            "purpose": "利用目的",
            "expected_start_date": "利用開始予定日",
            "expected_return_date": "返却予定日",
            "notes": "備考",
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("expected_start_date")
        end = cleaned_data.get("expected_return_date")
        if start and end and end < start:
            self.add_error("expected_return_date", "返却予定日は利用開始予定日以降にしてください。")
        return cleaned_data
