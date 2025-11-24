from django.shortcuts import render, redirect
from parser_programm.HHParser import HHParser
from parser_programm.RabotaRU import RabotaRU
from parser_programm.SuperJobParser import SuperJobParser
from django.views.generic import TemplateView, FormView, ListView
from django.urls import reverse_lazy

from aggregator.forms import SearchVacationForm


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

        for platform, parser_class in parsers.items():
            if platform in search_params['job_recruiter']:
                parser = parser_class()
                if platform == 'rabotaru':
                    vacancy_list = parser.parse_vacantions(search_params)
                    if vacancy_list != 'Not Found':
                        vacantions.extend(vacancy_list)
                    else:
                        return redirect('data_not_found')
                else:

                    for page in range(1, col_vac):
                        search_params['volume'] = page
                        print(int(search_params['volume']))
                        vacancy_list = parser.parse_vacantions(search_params)
                        if vacancy_list != 'Not Found':
                            vacantions.extend(vacancy_list)
                        else:
                            return redirect('data_not_found')

        print(f"Всего найдено вакансий: {len(vacantions)}")
        self.request.session['vacantions'] = vacantions

        return redirect('response_vacantions')


class ResponseVacations(TemplateView):
    template_name = 'aggregator/response_vacation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vacancies = self.request.session.get('vacantions', [])

        context['vacations'] = vacancies

        return context



