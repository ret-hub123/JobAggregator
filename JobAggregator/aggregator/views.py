from django.shortcuts import render, redirect
from parser_programm.HHParser import HHParser
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

        print(search_params['job_recruiter'])

        vacantions = []
        if 'headhunter' in search_params['job_recruiter']:
            par = HHParser()
            vacantion = par.parse_vacantions(search_params)
            if vacantion != 'Not Found':
                vacantions.append(vacantion)
            else:
                return redirect('data_not_found')

        if 'superjob' in search_params['job_recruiter']:
            par = SuperJobParser()
            vacantion = par.parse_vacantions(search_params)
            if vacantion != 'Not Found':
                vacantions.append(vacantion)
            else:
                return redirect('data_not_found')

        self.request.session['vacantions'] = vacantions

        return redirect('response_vacantions')

class ResponseVacations(TemplateView):
    template_name = 'aggregator/response_vacation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vacancies = self.request.session.get('vacantions', [])

        context['vacations'] = vacancies

        return context



