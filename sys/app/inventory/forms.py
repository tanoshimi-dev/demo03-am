from django import forms

from .models import InventoryResult, InventorySession


class InventorySessionForm(forms.ModelForm):
    class Meta:
        model = InventorySession
        fields = ["name", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "name": "セッション名",
            "notes": "メモ",
        }


class InventoryResultForm(forms.ModelForm):
    class Meta:
        model = InventoryResult
        fields = ["status", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 2}),
        }
        labels = {
            "status": "実査結果",
            "notes": "メモ",
        }
