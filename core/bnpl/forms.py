from django import forms
from accounts.models import  WeekDay
from bnpl.models import BnplAccount


class EditBnplAccountForm(forms.ModelForm):
    working_day = forms.MultipleChoiceField(
        choices=WeekDay.choices,
        widget=forms.CheckboxSelectMultiple(),
        required=False,
    )

    class Meta:
        model = BnplAccount
        fields = ['parslogic_account', 'agent_name', 'working_day', 'is_working']

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance and instance.pk:
            kwargs.setdefault('initial', {})
            kwargs['initial']['working_day'] = [str(d) for d in (instance.working_day or [])]
        super().__init__(*args, **kwargs)

        self.fields['parslogic_account'].disabled = True

    def clean_working_day(self):
        return [int(d) for d in self.cleaned_data['working_day']]