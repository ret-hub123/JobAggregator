from datetime import datetime

from parser_programm.Base_Parser import BaseParser


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

        if vacancy['salary']:
            if vacancy['salary']['to'] == None:
                salary_info = f"от {vacancy['salary']['from']} рублей"
            elif vacancy['salary']['from'] == None:
                salary_info = f"до {vacancy['salary']['to']} рублей"
            else:
                salary_info = f"в среднем {(vacancy['salary']['from'] + vacancy['salary']['to']) // 2} рублей"
        else: salary_info = 'Не указана'
        if vacancy['address']: address_info = f"{vacancy['address']['city']}, {vacancy['address']['street']}, {vacancy['address']['building']}"
        else: address_info = 'Нет информации о адресе'

        dt = datetime.fromisoformat(vacancy['published_at'])

        print(self.extract_education(vacancy['snippet']['requirement']))

        self.processed_vacancy = {
            'agregator': 'HeadHunter',
            'name': vacancy['name'],
            'company': vacancy['employer']['name'],
            'salary': salary_info,
            'address': address_info,
            'experience': f"{self.extract_experience(vacancy.get('experience', {}).get('name', 'Не указан'))}, {self.extract_education(vacancy.get('snippet', {}).get('requirement', 'Не указан'))}",
            'employment': vacancy['employment']['name'],
            'schedule': vacancy['work_schedule_by_days'][0]['name'],
            'url': vacancy['alternate_url'],
            'published_at': dt.strftime("%d.%m.%Y %H:%M"),
        }

        return self.processed_vacancy

    def extract_education(self, requirement_text):

        if not requirement_text:
            return "Не имеет значения"

        text_lower = requirement_text.lower()

        if 'высшее' in text_lower:
            return 'высшее образование'
        elif 'среднее профессиональное' in text_lower:
            return 'среднее профессиональное образование'
        elif 'среднее специальное' in text_lower:
            return 'среднее специальное образование'
        elif 'среднее' in text_lower:
            return 'среднее образование'
        elif 'неполное высшее' in text_lower:
            return 'неполное высшее образование'
        elif 'учен' in text_lower:
            return 'ученая степень'

        return "Не имеет значения"

    def extract_experience(self, requirement_text):

        if not requirement_text:
            return "Без опыта"

        if requirement_text == "От 1 года до 3 лет":
            return "От 1 года"
        if requirement_text == "От 3 до 6 лет":
            return "От 3 лет"
        if requirement_text == "Более 6 лет":
            return "От 6 лет"

        return "Без опыта"

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






