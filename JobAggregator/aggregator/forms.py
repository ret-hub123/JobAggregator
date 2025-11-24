from django import forms


JOB_RECRUITER_CHOICES = [
    ("headhunter", "HeadHunter"),
    ("superjob", "SuperJob"),
    ("rabotaru", "RabotaRU"),
]

class SearchVacationForm(forms.Form):
    job_recruiter = forms.MultipleChoiceField (
        choices=JOB_RECRUITER_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label="Площадка для поиска вакансий"
    )
    keywords = forms.CharField(label='Наименование должности', widget=forms.TextInput(attrs={'class': 'search-form'}))
    area = forms.CharField(label='Город', widget=forms.TextInput(attrs={'class': 'search-form'}))
    period = forms.IntegerField(label='Период поиска', widget=forms.NumberInput(attrs={'class': 'search-form'}))
    volume = forms.IntegerField(label='Количество вакансий с ресурса', widget=forms.NumberInput(attrs={'class': 'search-form'}))

    class Meta:
        fields = ['job_recruiter', 'keywords', 'area', 'period', 'volume']
