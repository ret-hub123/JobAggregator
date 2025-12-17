from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

User = get_user_model()


class Vacation(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='vacancies', verbose_name='Пользователь')
    aggregator = models.CharField(max_length=50,verbose_name='Платформа',
        choices=[ ('HeadHunter', 'HeadHunter'), ('SuperJob', 'SuperJob'), ('Rabota.ru', 'Rabota.ru'),])

    name = models.CharField(max_length=255, verbose_name='Название вакансии')
    company = models.CharField(max_length=255, verbose_name='Компания')
    salary = models.IntegerField(null=True, blank=True, verbose_name='Зарплата')
    address = models.TextField(verbose_name='Адрес', blank=True, default="Не указано")
    experience = models.CharField(max_length=100, verbose_name='Опыт работы',
    choices = [('not_experience', 'Нет опыта'), ('1year', 'От 1 года'),('3year', 'От 3 лет'),('6year', 'От 6 лет'),('10year', 'От 10 лет'),],
    default = 'not_experience')
    education = models.CharField(
    max_length=50, verbose_name='Образование',
    choices=[('not_important', 'Не имеет значения'),('secondary', 'среднее профессиональное образование'),('higher', 'высшее образование'),('half_higher', 'неполное высшее'),('any', 'образование любое'),],
    default='Не имеет значения')

    is_favorite = models.BooleanField(default=False,verbose_name='В избранном')

    employment = models.CharField(max_length=100, verbose_name='Тип занятости',
        choices=[('not_specified', 'Не имеет значения'),('full_day', 'Полная занятость'),('no_full_day', 'Неполная занятость'),('no_full_day', 'сменный график')],
        default='not_specified')
    schedule = models.CharField(
        max_length=20, verbose_name='График работы',
        choices=[('not_specified', 'Не имеет значения'),('5/2', '5/2'),('2/2', '2/2'),('15/15', '15/15'),('20/10', '20/10'),],
        default='not_specified')

    url = models.URLField(max_length=500, verbose_name='Ссылка на вакансию')
    published_at = models.DateTimeField(verbose_name='Дата публикации')

    class Meta:
        unique_together = ['user', 'url']

    def __str__(self):
        return f"{self.name} - {self.company}"

    def change_favorite(self):
        self.is_favorite = not self.is_favorite
        self.save()
        return self.is_favorite




class SearchQuery(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='search_queries',
        verbose_name='Пользователь'
    )


    query = models.CharField(
        max_length=255,
        verbose_name='Поисковый запрос'
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Город'
    )

    platforms = models.JSONField(
        default=list,
        verbose_name='Выбранные платформы'
    )

    total_results = models.IntegerField(
        default=0,
        verbose_name='Всего найдено'
    )


    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата и время поиска'

    )


    vacancies = models.ManyToManyField(
        Vacation,
        related_name='search_queries',
        blank=True,
        verbose_name='Найденные вакансии'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Поисковый запрос'

    def __str__(self):
        return f"{self.user.username}: {self.query} ({self.created_at})"
