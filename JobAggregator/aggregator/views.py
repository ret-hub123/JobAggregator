from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from parser_programm.HH_Parser import HHParser
from parser_programm.Rabota_RU import RabotaRU
from parser_programm.Super_Job_Parser import SuperJobParser
from django.views.generic import TemplateView, FormView
from aggregator.forms import SearchVacationForm
from aggregator.models import Vacation, SearchQuery
from django.utils import timezone
from datetime import datetime
from django.contrib import messages

from aggregator.forms import VacancyFilterForm

from aggregator.statistics import Statistic


class Index(TemplateView):
    template_name = 'aggregator/main.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user if self.request.user.is_authenticated else None

        context['title'] = "Добро пожаловать!"
        context['last_favorite'] = Vacation.objects.filter(
            user=user,
            is_favorite=True
        ).order_by('-published_at')[:2]
        return context



class DataNotFound(TemplateView):
    template_name = 'aggregator/data_not_found.html'


class FavouritesVacation(TemplateView):
    template_name = 'aggregator/favorite_vacantion.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user if self.request.user.is_authenticated else None

        if user:

            context['vacations'] = Vacation.objects.filter(
                user=user,
                is_favorite=True
            )
        else:
            context['vacations'] = Vacation.objects.none()

        context['title'] = 'Избранные вакансии'
        return context

    def post(self, request):

        # Получаем ID вакансии из POST-запроса
        vacation_id = request.POST.get('vacation_id')

        if vacation_id:
            try:
                # Находим вакансию текущего пользователя
                vacation = Vacation.objects.get(
                    id=vacation_id,
                    user=request.user
                )

                # Используем метод модели
                new_status = vacation.change_favorite()

                return redirect('response_vacantions')


            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
                return redirect('favorites_vacations')

        return redirect('favorites_vacations')


class SearchVacantions(FormView):
    form_class = SearchVacationForm
    template_name = 'aggregator/search_vacations.html'

    def form_valid(self, form):
        search_params = form.cleaned_data
        self.request.session['search_params'] = search_params
        col_vac = int(search_params['volume']) + 1

        print(search_params)

        parsers = {
            'headhunter': HHParser,
            'superjob': SuperJobParser,
            'rabotaru': RabotaRU,
        }

        user = self.request.user if self.request.user.is_authenticated else None

        saved_vacancy_ids = []
        saved_vacancy_objects = []

        for platform, parser_class in parsers.items():
            if platform in search_params['job_recruiter']:
                parser = parser_class()
                if platform == 'rabotaru':
                    vacancy = parser.parse_vacantions(search_params)
                    if vacancy != 'Not Found':
                        saved_objs = self.save_vacancies(vacancy, platform, user)
                        if saved_objs:
                            saved_vacancy_objects.extend(saved_objs)
                            saved_vacancy_ids.extend([obj.id for obj in saved_objs])
                    else:
                        return redirect('data_not_found')
                else:
                    for page in range(1, col_vac):
                        search_params['volume'] = page

                        vacancy = parser.parse_vacantions(search_params)
                        if vacancy != 'Not Found':
                            saved_objs = self.save_vacancies([vacancy], platform, user)
                            if saved_objs:
                                saved_vacancy_objects.extend(saved_objs)
                                saved_vacancy_ids.extend([obj.id for obj in saved_objs])
                        else:
                            return redirect('data_not_found')

        print(f"Всего найдено вакансий: {len(saved_vacancy_ids)}")

        # Сохраняем в сессию только ID вакансий
        self.request.session['vacancy_ids'] = saved_vacancy_ids

        if user and user.is_authenticated and saved_vacancy_objects:
            self.create_search_query(user, search_params, saved_vacancy_objects)

        return redirect('response_vacantions')

    def save_vacancies(self, vacancies, platform, user):
        saved_objects = []
        if not user or not user.is_authenticated:
            print("Пользователь не авторизован. Вакансии не будут сохранены.")
            return saved_objects

        platform_map = {
            'headhunter': 'HeadHunter',
            'superjob': 'SuperJob',
            'rabotaru': 'Rabota.ru',
        }

        aggregator_name = platform_map.get(platform, platform)

        for vacancy_data in vacancies:
            try:

                date_str = vacancy_data.get('published_at')
                if date_str:
                    dt = datetime.strptime(date_str, '%d.%m.%Y %H:%M')
                    published_at = timezone.make_aware(dt, timezone.get_current_timezone())
                else:
                    published_at = timezone.now()

                print(vacancy_data)
                experience, education = vacancy_data.get('experience', 'not_experience').split(',')
                vacancy_obj, created = Vacation.objects.get_or_create(
                    user=user,
                    url=self.normal_url(vacancy_data['url']),
                    defaults={
                        'aggregator': aggregator_name,
                        'name': vacancy_data.get('name', ''),
                        'company': vacancy_data.get('company', ''),
                        'salary': self.parse_salary(vacancy_data.get('salary')),
                        'address': vacancy_data.get('address', ''),
                        'experience': experience,
                        'education': education,
                        'employment': vacancy_data.get('employment', 'not_specified'),
                        'schedule': vacancy_data.get('schedule', 'not_specified'),
                        'published_at': published_at,
                        'is_favorite': False,
                    }
                )

                saved_objects.append(vacancy_obj)
                print(f"Вакансия сохранена: {vacancy_data.get('name')}")

            except Exception as e:
                print(f"Ошибка при сохранении вакансии: {e}")
                print(f"Данные вакансии: {vacancy_data}")

        return saved_objects

    def parse_salary(self, salary_data):
        if not salary_data:
            return None

        try:
            if isinstance(salary_data, (int, float)):
                return int(salary_data)

            if isinstance(salary_data, str):
                import re
                salary_data = salary_data.replace(' ', '')
                numbers = re.findall(r'\d+', salary_data)
                if numbers:
                    return int(numbers[0])
        except Exception as e:
            print(f"Ошибка парсинга зарплаты: {e}")

        return None

    def normal_url(self, url=str):
        url_split = url.split('?')
        normalize_url = url_split[0]
        return normalize_url

    def create_search_query(self, user, search_params, vacancy_objects):
        try:
            search_query = SearchQuery.objects.create(
                user=user,
                query=search_params.get('keywords', ''),
                city=search_params.get('area', ''),
                platforms=search_params.get('job_recruiter', []),
                total_results=len(vacancy_objects)
            )

            search_query.vacancies.add(*vacancy_objects)
            search_query.save()


            self.request.session['last_search_query_id'] = search_query.id

            return search_query

        except Exception as e:
            print(f"Ошибка при создании SearchQuery: {e}")
            return None


class ResponseVacations(TemplateView):
    template_name = 'aggregator/response_vacation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем ID вакансий из сессии
        vacancy_ids = self.request.session.get('vacancy_ids', [])

        if vacancy_ids:
            # Получаем объекты Vacation по ID
            vacations = Vacation.objects.filter(id__in=vacancy_ids)
        else:
            vacations = Vacation.objects.none()

        filter_form = VacancyFilterForm(self.request.GET or None)

        platform = None
        sort_by = None
        experience = None

        if filter_form.is_valid():
            platform = filter_form.cleaned_data.get('platform')
            sort_by = filter_form.cleaned_data.get('sort_by')
            experience = filter_form.cleaned_data.get('experience')


        if platform:
            vacations = vacations.filter(aggregator=platform)

        if sort_by == 'salary_asc':
            vacations = vacations.order_by('salary')
        elif sort_by == 'salary_asc':
            vacations = vacations.order_by('-salary')


        if experience:
            if experience == 'not_experience':
                vacations = vacations.filter(experience='Без опыта')
            elif experience == '1year':
                vacations = vacations.filter(
                    experience__in=['От 1 года', 'От 3 лет', 'От 6 лет', 'От 10 лет']
                )
            elif experience == '3year':
                vacations = vacations.filter(
                    experience__in=['От 3 лет', 'От 6 лет', 'От 10 лет']
                )
            elif experience == '6year':
                vacations = vacations.filter(
                    experience__in=['От 6 лет', 'От 10 лет']
                )
            elif experience == '10year':
                vacations = vacations.filter(experience='От 10 лет')

        print(vacations.values_list)
        if vacations.exists():
            self.request.session['filtered_vacancy_ids'] = list(vacations.values_list('id', flat=True))
        else:
            self.request.session['filtered_vacancy_ids'] = []

        context['filter_form'] = filter_form
        context['vacations'] = vacations
        context['title'] = 'Результаты поиска вакансий'

        return context

    def post(self, request):

        vacation_id = request.POST.get('vacation_id')

        if vacation_id:
            try:
                # Находим вакансию текущего пользователя
                vacation = Vacation.objects.get(
                    id=vacation_id,
                    user=request.user
                )

                # Используем метод модели
                vacation.change_favorite()

                # Возвращаем на ту же страницу результатов
                return redirect('response_vacantions')

            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
                return redirect('response_vacantions')

        return redirect('response_vacantions')


class StatisticPage(TemplateView):
    template_name = 'aggregator/statistics_page.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        last_search_query = SearchQuery.objects.filter(
            user=self.request.user
        ).order_by('-created_at').first()

        if last_search_query:
            vacations = last_search_query.vacancies.all()


        filtered_vacancy_ids = self.request.session.get('filtered_vacancy_ids')
        print(filtered_vacancy_ids)
        if filtered_vacancy_ids and isinstance(filtered_vacancy_ids[0], list):
            filtered_vacancy_ids = [int(i[0]) for i in filtered_vacancy_ids]


        if filtered_vacancy_ids:
            vacations = vacations.filter(id__in=filtered_vacancy_ids)

        stat = Statistic(vacations)
        context['stat'] = stat.get_base_statistics()
        context['title'] = 'Статистика'

        return context