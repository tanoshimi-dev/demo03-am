from django import forms

from .models import IncidentReport


class IncidentReportForm(forms.ModelForm):
    class Meta:
        model = IncidentReport
        fields = ["incident_type", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "incident_type": "インシデント種別",
            "description": "内容",
        }


class IncidentResolveForm(forms.Form):
    resolution_notes = forms.CharField(
        required=False,
        label="解決メモ",
        widget=forms.Textarea(attrs={"rows": 4}),
    )
