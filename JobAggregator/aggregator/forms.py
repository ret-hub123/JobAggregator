from django import forms


JOB_RECRUITER_CHOICES = [
    ("headhunter", "HeadHunter"),
    ("superjob", "SuperJob"),
]

class SearchVacationForm(forms.Form):
    job_recruiter = forms.MultipleChoiceField (
        choices=JOB_RECRUITER_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label="Площадка для поиска вакансий"
    )
    keywords = forms.CharField(label='Наименование должности', widget=forms.TextInput(attrs={'class': 'search-form'}))
    area = forms.IntegerField(label='Город', widget=forms.NumberInput(attrs={'class': 'search-form'}))
    period = forms.IntegerField(label='Период поиска', widget=forms.NumberInput(attrs={'class': 'search-form'}))
    page = forms.IntegerField(label='Номер страницы', widget=forms.NumberInput(attrs={'class': 'search-form'}))

    class Meta:
        fields = ['job_recruiter', 'keywords', 'area', 'period', 'page']
