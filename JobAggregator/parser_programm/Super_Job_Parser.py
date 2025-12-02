import datetime
from parser_programm.Base_Parser import BaseParser


class SuperJobParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.superjob.ru/2.0"
        self.api_key = "v3.r.139361338.b537d7f8cc426e40e05e66d2e9d8961dd504351a.4e3767e4fea9205c34c41f95a9fa85ee729ca178"


        self.session.headers.clear()
        self.session.headers.update({
            'X-Api-App-Id': self.api_key,
            'Content-Type': 'application/x-www-form-urlencoded',
        })

    def parse_vacantions(self, search_params):
        url = f"{self.base_url}/vacancies/"


        town_code = TOWN_CODES.get(search_params.get('area', 'Москва'), 4)

        params = {
            "keyword": search_params.get('keywords', ''),
            "town": town_code,
            "period": search_params.get('period', 30),
            "count": search_params.get('volume', 1),
            "page": 0,
        }

        response = self.get_response('GET', url, params=params)

        if response:
            data = response.json()
            return self.detail_data_vacation(data)
        return None

    def extract_education(self, requirement_text):

        if not requirement_text:
            return "Не указано"

        text_lower = requirement_text.lower()

        if 'высшее' in text_lower:
            return 'Высшее образование'
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

        return "Не указано"



    def detail_data_vacation(self, data):
        if not data.get('objects'):
            return 'Not Found'

        vacancy = data['objects'][0]

        print(vacancy)

        salary_info = self._format_salary(vacancy)

        published_date = self._format_date(vacancy.get('date_published'))

        processed_vacancy = {
            'agregator': 'SuperJob',
            'name': vacancy.get('profession', 'Не указано'),
            'company': vacancy.get('firm_name', 'Не указано'),
            'salary': salary_info,
            'address': vacancy.get('address', 'Не указан'),
            'experience': f"{vacancy.get('experience', {}).get('title', 'Не указан')}, {self.extract_education(vacancy.get('education', {}).get('title', 'Не указан'))}",
            'employment': 'Полная занятость' if vacancy.get('type_of_work', {}).get('title', 'Не указана') == 'Полный рабочий день' else 'Не имеет значения',
            'schedule':  self.extract_schedule(vacancy),
            'url': vacancy.get('link', ''),
            'published_at': published_date,
        }

        return processed_vacancy

    def extract_schedule(self, vacancy_data):

        text = vacancy_data.get('candidat', '').lower()

        if '5/2' in text or '5/2' in vacancy_data.get('vacancyRichText', '').lower():
            return '5/2'
        elif '2/2' in text or '2/2' in vacancy_data.get('vacancyRichText', '').lower():
            return '2/2'
        elif '15/15' in text or '15/15' in vacancy_data.get('vacancyRichText', '').lower():
            return '15/15'
        elif '20/10' in text or '20/10' in vacancy_data.get('vacancyRichText', '').lower():
            return '20/10'
        else:
            return vacancy_data.get('place_of_work', {}).get('title', 'Не указана')


    def _format_salary(self, vacancy):

        payment_from = vacancy.get('payment_from')
        payment_to = vacancy.get('payment_to')


        if payment_from and payment_to:
            return f"в среднем {(payment_from + payment_to) // 2} рублей"
        elif payment_from:
            return f"от {payment_from} рублей"
        elif payment_to:
            return f"до {payment_to} рублей"
        return "Не указана"

    def _format_date(self, timestamp):

        if timestamp:
            try:
                dt = datetime.datetime.fromtimestamp(timestamp)
                return dt.strftime("%d.%m.%Y %H:%M")
            except (ValueError, TypeError):
                return "Не указана"
        return "Не указана"

    def extract_education(self, requirement_text):

        if not requirement_text:
            return "Не имеет значения"

        text_lower = requirement_text.lower()
        print(text_lower)
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


TOWN_CODES = {
    "Москва": 4,
    "Санкт-Петербург": 14,
    "Новосибирск": 13,
    "Екатеринбург": 33,
    "Нижний Новгород": 47,
    "Казань": 88,
    "Челябинск": 104,
    "Омск": 68,
    "Самара": 78,
    "Ростов-на-Дону": 76,
    "Уфа": 99,
    "Красноярск": 54,
    "Пермь": 72,
    "Воронеж": 26,
    "Волгоград": 24,
    "Краснодар": 1438,
    "Саратов": 1596,
}