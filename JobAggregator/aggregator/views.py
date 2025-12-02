from django.shortcuts import redirect
from parser_programm.HH_Parser import HHParser
from parser_programm.Rabota_RU import RabotaRU
from parser_programm.Super_Job_Parser import SuperJobParser
from django.views.generic import TemplateView, FormView
from aggregator.forms import SearchVacationForm
from aggregator.models import Vacation
from django.utils import timezone
from datetime import datetime



class Index(TemplateView):
    template_name =  'aggregator/main.html'
    extra_context = {'title': "Главная страница"}


class DataNotFound(TemplateView):
    template_name = 'aggregator/data_not_found.html'


class SearchVacantions(FormView):
    form_class = SearchVacationForm
    template_name = 'aggregator/search_vacations.html'

    def form_valid(self, form):
        search_params = form.cleaned_data
        self.request.session['search_params'] = search_params
        col_vac = int(search_params['volume']) + 1

        print(search_params)

        vacantions = []
        parsers = {
            'headhunter': HHParser,
            'superjob': SuperJobParser,
            'rabotaru': RabotaRU,
        }

        user = self.request.user if self.request.user.is_authenticated else None

        for platform, parser_class in parsers.items():
            if platform in search_params['job_recruiter']:
                parser = parser_class()
                if platform == 'rabotaru':
                    vacancy = parser.parse_vacantions(search_params)
                    if vacancy != 'Not Found':
                        vacantions.extend(vacancy)
                        self.save_vacancies(vacancy, platform, user)
                    else:
                        return redirect('data_not_found')
                else:
                    for page in range(1, col_vac):
                        search_params['volume'] = page
                        print(int(search_params['volume']))
                        vacancy = parser.parse_vacantions(search_params)
                        if vacancy != 'Not Found':
                            vacantions.append(vacancy)
                            self.save_vacancies([vacancy], platform, user)
                        else:
                            return redirect('data_not_found')

        print(f"Всего найдено вакансий: {len(vacantions)}")
        self.request.session['vacantions'] = vacantions

        return redirect('response_vacantions')


    def save_vacancies(self, vacancies, platform, user):
        if not user or not user.is_authenticated:
            print("Пользователь не авторизован. Вакансии не будут сохранены.")
            return

        platform_map = {
            'headhunter': 'HeadHunter',
            'superjob': 'SuperJob',
            'rabotaru': 'Rabota.ru',
        }

        aggregator_name = platform_map.get(platform, platform)

        for vacancy_data in vacancies:
            try:
                if 'url' not in vacancy_data:
                    continue


                date_str = vacancy_data.get('published_at')
                if date_str:

                    dt = datetime.strptime(date_str, '%d.%m.%Y %H:%M')

                    published_at = timezone.make_aware(dt, timezone.get_current_timezone())
                else:
                    published_at = timezone.now()

                Vacation.objects.update_or_create(
                    user=user,
                    url= self.normal_url(vacancy_data['url']),
                    defaults={
                        'aggregator': aggregator_name,
                        'name': vacancy_data.get('name', ''),
                        'company': vacancy_data.get('company', ''),
                        'salary': self.parse_salary(vacancy_data.get('salary')),
                        'address': vacancy_data.get('address', ''),
                        'experience': vacancy_data.get('experience', 'not_experience'),
                        'education': vacancy_data.get('education', 'not_important'),
                        'employment': vacancy_data.get('employment', 'not_specified'),
                        'schedule': vacancy_data.get('schedule', 'not_specified'),
                        'published_at': published_at,
                    }
                )
                print(f"Вакансия сохранена: {vacancy_data.get('name')}")

            except Exception as e:
                print(f"Ошибка при сохранении вакансии: {e}")
                print(f"Данные вакансии: {vacancy_data}")

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


    def normal_url(self, url = str):

        url_split = url.split('?')
        normalize_url = url_split[0]
        print(normalize_url)

        return normalize_url



class ResponseVacations(TemplateView):
    template_name = 'aggregator/response_vacation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vacancies = self.request.session.get('vacantions', [])

        context['vacations'] = vacancies

        return context



