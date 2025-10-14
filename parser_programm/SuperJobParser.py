import datetime

from parser_programm.BaseParser import BaseParser
from parser_programm.secret_key_orzanization_SuperJob import get_key_access

class SuperJobParser(BaseParser):

    def __init__(self):
        super().__init__()
        self.base_url = "https://api.superjob.ru/2.0/vacancies/"
        self.headers = get_key_access()

    def parse_vacantions(self, search_params):
        params = {
            "keyword": search_params.get("keyword"),
            "town": search_params.get("town"),
            "count": 1,

        }

        response = self.get_response('GET', self.base_url, params = params, headers =  self.headers)

        if response:
            data = response.json()
            return self.detail_data_vacation(data)
        return None

    def detail_data_vacation(self, vacancy):


            if not vacancy['objects'][0]['is_closed']:
                vacancy = vacancy['objects'][0]
            else:
                return 'Not Found'

            if vacancy['payment_from']:
                salary_info = f"{vacancy['payment_from']} - {vacancy['payment_to']}"
            else:
                salary_info = 'Нет информации по зарплате'
            if vacancy['address']:
                address_info = vacancy['address']
            else:
                address_info = 'Нет информации о адресе'

            published_date = datetime.datetime.fromtimestamp(vacancy['date_published'])

            self.processed_vacancy = {
                'name': vacancy['profession'],
                'company': vacancy['client']['title'],
                'salary': salary_info,
                'address': address_info,
                'experience': vacancy['experience']['title'],
                'employment': vacancy['place_of_work']['title'],
                'schedule': vacancy['type_of_work']['title'],
                'url': vacancy['link'],
                'published_at': published_date.strftime('%Y-%m-%d %H:%M:%S'),
            }

            return self.processed_vacancy

params = {
            "keyword": "Бухгалтер",
            "town": 5,
        }

par = SuperJobParser()
par.parse_vacantions(params)