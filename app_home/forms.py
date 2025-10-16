from django import forms
from app_kiberclub.models import Branch, Location

class UploadFileForm(forms.Form):
    branch = forms.ModelChoiceField(queryset=Branch.objects.all(), label="Филиал")
    location = forms.ModelChoiceField(queryset=Location.objects.none(), label="Локация")
    file = forms.FileField(label="Файл", required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'branch' in self.data:
            try:
                branch_id = int(self.data.get('branch'))
                self.fields['location'].queryset = Location.objects.filter(branch_id=branch_id).order_by('name')
            except (ValueError, TypeError):
                pass  # invalid input from browser; ignore and fallback to empty Location queryset


    def clean(self):
        cleaned_data = super().clean()
        branch = cleaned_data.get("branch")
        location = cleaned_data.get("location")

        if branch and location:
            if location.branch != branch:
                raise forms.ValidationError(
                    "Выбранная локация не принадлежит выбранному филиалу."
                )
        return cleaned_data

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file and not file.name.endswith('.xlsx'):
            raise forms.ValidationError("Можно загружать только файлы с расширением .xlsx")
        return file