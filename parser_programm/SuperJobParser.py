import datetime
import requests
from parser_programm.BaseParser import BaseParser


class SuperJobParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.superjob.ru/2.0"
        # Получите новый ключ через регистрацию
        self.api_key = "YOUR_NEW_API_KEY_HERE"  # ЗАМЕНИТЕ НА НОВЫЙ КЛЮЧ

        # Полная очистка и переустановка заголовков
        self.session.headers.clear()
        self.session.headers.update({
            'X-Api-App-Id': self.api_key,
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def parse_vacantions(self, search_params):
        # Правильный endpoint
        url = f"{self.base_url}/vacancies/"

        params = {
            "keyword": search_params.get('keywords', ''),
            "town": TOWN_CODES.get(search_params.get('area', 'Москва'), 4),
            "period": self._get_period_id(search_params.get('period', 30)),
            "count": 1,  # количество вакансий
            "page": 0,  # страница
        }

        print(f"🔍 SuperJob API Request:")
        print(f"URL: {url}")
        print(f"Params: {params}")
        print(f"Headers: {dict(self.session.headers)}")

        try:
            response = self.session.get(url, params=params, timeout=10)
            print(f"📊 Response Status: {response.status_code}")
            print(f"📄 Response Headers: {dict(response.headers)}")
            print(f"📝 Response Text: {response.text[:500]}...")  # первые 500 символов

            if response.status_code == 200:
                data = response.json()

                # Проверяем наличие ошибки в теле ответа
                if 'error' in data:
                    print(f"❌ API Error in response: {data['error']}")
                    return None

                return self.detail_data_vacation(data)
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None

    def _get_period_id(self, period):
        period_mapping = {
            1: 1, 7: 7, 30: 30,
            'day': 1, 'week': 7, 'month': 30
        }
        return period_mapping.get(period, 30)

    def detail_data_vacation(self, data):
        if not data.get('objects'):
            print("❌ No vacancies found")
            return None

        vacancy = data['objects'][0]

        # Форматируем данные
        salary_info = self._format_salary(vacancy)

        processed_vacancy = {
            'agregator': 'SuperJob',
            'name': vacancy.get('profession', 'Не указано'),
            'company': vacancy.get('client', {}).get('title', 'Не указано'),
            'salary': salary_info,
            'address': vacancy.get('address', 'Не указан'),
            'experience': vacancy.get('experience', {}).get('title', 'Не указан'),
            'employment': vacancy.get('place_of_work', {}).get('title', 'Не указана'),
            'schedule': vacancy.get('type_of_work', {}).get('title', 'Не указан'),
            'url': vacancy.get('link', ''),
            'published_at': self._format_date(vacancy.get('date_published')),
        }

        return processed_vacancy

    def _format_salary(self, vacancy):
        salary_from = vacancy.get('payment_from')
        salary_to = vacancy.get('payment_to')
        currency = vacancy.get('currency', 'rub')

        if salary_from and salary_to:
            return f"{salary_from} - {salary_to} {currency}"
        elif salary_from:
            return f"от {salary_from} {currency}"
        elif salary_to:
            return f"до {salary_to} {currency}"
        return "Не указана"

    def _format_date(self, timestamp):
        if timestamp:
            dt = datetime.datetime.fromtimestamp(timestamp)
            return dt.strftime("%d.%m.%Y %H:%M")
        return "Не указана"


TOWN_CODES = {
    "Москва": 4,
    "Санкт-Петербург": 14,
    "Новосибирск": 13,
    "Екатеринбург": 33,
    # ... остальные города
}