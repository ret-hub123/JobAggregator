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
            'area': TOWN_CODES[search_params.get('area')],
            'period': search_params.get('period', 30),
            'page': search_params.get('volume', 1),

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

        if vacancy['salary']: salary_info = f"{vacancy['salary']['from']} - {vacancy['salary']['to']}"
        else: salary_info = 'Нет информации по зарплате'
        if vacancy['address']: address_info = f"{vacancy['address']['city']}, {vacancy['address']['street']}, {vacancy['address']['building']}"
        else: address_info = 'Нет информации о адресе'

        dt = datetime.fromisoformat(vacancy['published_at'])

        self.processed_vacancy = {
            'agregator': 'HeadHunter',
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



TOWN_CODES = {
    "Москва": 1,
    "Санкт-Петербург": 2,
    "Новосибирск": 4,
    "Екатеринбург": 3,
    "Владимир": 23,
    "Нижний Новгород": 66,
    "Ростов-на-Дону": 76,
    "Хабаровск": 102,
    "Казань": 88,
    "Челябинск": 104,
    "Омск": 68,
    "Самара": 78,
    "Уфа": 99,
    "Красноярск": 54,
    "Пермь": 72,
    "Воронеж": 26,
    "Волгоград": 24,
    "Саратов": 1596,
    "Краснодар": 1438,
}






