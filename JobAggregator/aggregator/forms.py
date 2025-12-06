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


class VacancyFilterForm(forms.Form):
    PLATFORM_CHOICES = [
        ('', 'Все платформы'),
        ('HeadHunter', 'HeadHunter'),
        ('SuperJob', 'SuperJob'),
        ('Rabota.ru', 'Rabota.ru'),
    ]

    EXPERIENCE_CHOICES = [
        ('', 'Любой опыт'),
        ('not_experience', 'Нет опыта'),
        ('1year', 'От 1 года'),
        ('3year', 'От 3 лет'),
        ('6year', 'От 6 лет'),
        ('10year', 'От 10 лет'),
    ]

    platform = forms.ChoiceField(
        choices=PLATFORM_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    min_salary = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control','placeholder': 'От',})
    )

    max_salary = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control','placeholder': 'До', })
    )

    experience = forms.ChoiceField(
        choices=EXPERIENCE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    SORT_CHOICES = [
        ('', 'Без сортировки'),
        ('salary_asc', 'Зарплата по возрастанию'),
        ('salary_desc', 'Зарплата по убыванию'),
    ]

    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        min_salary = cleaned_data.get('min_salary')
        max_salary = cleaned_data.get('max_salary')

        if min_salary and max_salary and min_salary > max_salary:
            raise forms.ValidationError("Минимальная зарплата не может быть больше максимальной")

        return cleaned_data