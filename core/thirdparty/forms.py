from django import forms
from accounts.models import ProfileThpIssuingAgent , WeekDay

class EditIssuingAgentForm(forms.ModelForm):
    working_days = forms.MultipleChoiceField(
        choices=WeekDay.choices,
        widget=forms.CheckboxSelectMultiple(),
        required=False,
    )

    class Meta:
        model = ProfileThpIssuingAgent
        fields = [
            'person_name', 'capacity', 'start_shift', 'end_shift',
            'working_days', 'working_insurance_company', 'working_category',
            'is_working', 'is_visible'
        ]
        widgets = {
            'working_insurance_company': forms.CheckboxSelectMultiple(),
            'working_category': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['working_days'].initial = [
                str(day) for day in self.instance.working_days
            ]

    def clean_working_days(self):
        data = self.cleaned_data['working_days']
        return [int(day) for day in data]