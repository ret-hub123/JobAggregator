from datetime import datetime
from http.client import HTTPResponse

from django.http import HttpResponse
from django.shortcuts import redirect

from parser_programm.BaseParser import BaseParser

class HHParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.hh.ru/vacancies"

    def parse_vacantions(self, search_params):
        params = {
            'text': search_params.get('keywords', ''),
            'area': search_params.get('area', 1),
            'period': search_params.get('period', 20),
            'per_page': search_params.get('per_page', 1),
            'page': search_params.get('page', 0)
        }

        response = self.get_response('GET', self.base_url, params = params)
        if response:
            data = response.json()
            return self.detail_data_vacation(data)
        return None

    def detail_data_vacation(self, vacancy):

        if vacancy['items']:
            vacancy = vacancy['items'][0]
        else:
            return 'Not Found'

        if vacancy['salary']: salary_info = vacancy['salary']
        else: salary_info = 'Нет информации по зарплате'
        if vacancy['address']: address_info = vacancy['address']
        else: address_info = 'Нет информации о адресе'

        dt = datetime.fromisoformat(vacancy['published_at'])

        self.processed_vacancy = {
            'name': vacancy['name'],
            'company': vacancy['employer']['name'],
            'salary': salary_info,
            'address': address_info,
            'experience': vacancy['experience']['name'],
            'employment': vacancy['employment']['name'],
            'schedule': vacancy['schedule']['name'],
            'url': vacancy['alternate_url'],
            'published_at': dt.strftime("%d.%m.%Y %H:%M"),
        }

        return self.processed_vacancy




