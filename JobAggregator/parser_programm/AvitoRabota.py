from bs4 import BeautifulSoup
import time
import random
import requests
from parser_programm.Base_Parser import BaseParser


class AvitoRabota(BaseParser):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.avito.ru"

        # Настройки защиты от блокировок
        self.request_delay = random.uniform(3, 7)  # увеличиваем задержку
        self.connect_timeout = 10
        self.read_timeout = 30
        self.max_retries = 2  # уменьшаем попытки для Avito

        self.TOWN_PREFIXES = {
            "москва": "moskva",
            "санкт-петербург": "sankt-peterburg",
            "брянск": "bryansk",
            "владивосток": "vladivostok",
            "екатеринбург": "ekaterinburg",
            "казань": "kazan",
            "краснодар": "krasnodar",
            "красноярск": "krasnoyarsk",
            "нижний новгород": "nnov",
            "новосибирск": "nsk",
            "омск": "omsk",
            "пермь": "perm",
            "ростов-на-дону": "rostov",
            "самара": "samara",
            "уфа": "ufa",
            "челябинск": "chelyabinsk"
        }

    def get_safe_response(self, method, url, **kwargs):
        """Безопасный запрос с обработкой блокировок Avito"""
        for attempt in range(self.max_retries):
            try:
                # Меняем User-Agent для каждого запроса
                self.session.headers['User-Agent'] = random.choice(self.user_agents)

                # Случайная задержка
                delay = random.uniform(3, 8)
                print(f"🕐 Waiting {delay:.1f} seconds before request...")
                time.sleep(delay)

                # Устанавливаем таймауты
                kwargs['timeout'] = (self.connect_timeout, self.read_timeout)

                response = self.session.request(method, url, **kwargs)

                # Обработка 429 ошибки
                if response.status_code == 429:
                    print("🚫 Avito blocked us (429). Waiting longer...")
                    time.sleep(random.uniform(30, 60))  # долгая пауза
                    continue

                # Обработка 403 ошибки
                if response.status_code == 403:
                    print("🚫 Access forbidden (403). Possible IP ban.")
                    return None

                response.raise_for_status()
                return response

            except requests.exceptions.HTTPError as e:
                if '429' in str(e):
                    print(f"🚫 HTTP 429 error (attempt {attempt + 1})")
                    time.sleep(random.uniform(30, 60))
                    continue
                else:
                    print(f"❌ HTTP error: {e}")
                    return None

            except requests.exceptions.RequestException as e:
                print(f"❌ Request error: {e}")
                return None

        print(f"❌ All {self.max_retries} attempts failed")
        return None

    def parse_vacantions(self, search_params):
        # Формируем параметры запроса
        params = {
            'q': search_params.get('keywords', ''),
        }

        # Добавляем параметр для вакансий, если нужно
        params['s'] = '104'  # раздел "Работа" на Avito

        # Формируем URL
        area_lower = search_params.get('area', '').lower()
        if area_lower in self.TOWN_PREFIXES:
            self.town_url = f"{self.base_url}/{self.TOWN_PREFIXES[area_lower]}"
        else:
            self.town_url = self.base_url

        print(f"🎯 Target URL: {self.town_url}")
        print(f"🔍 Search params: {params}")

        # Используем безопасный запрос
        response = self.get_safe_response('GET', self.town_url, params=params)

        # Проверяем ответ
        if response is None:
            print("❌ No response received - Avito might be blocking us")
            return []

        print(f"✅ Success! Final URL: {response.url}")
        print(f"📊 Status Code: {response.status_code}")

        # Проверяем не вернула ли нас Avito на главную страницу
        if 'avito.ru' in response.url and '/rabota' not in response.url:
            print("⚠️  Avito redirected to main page - might be blocking job searches")

        soup = BeautifulSoup(response.text, 'html.parser')
        vacancies_data = []

        # Пробуем разные селекторы для карточек вакансий
        possible_selectors = [
            'div[data-marker*="vacancy"]',
            '.iva-item-root',
            '.styles-module-theme-_IJ5n',
            '[data-marker*="item"]'
        ]

        vacancy_cards = []
        for selector in possible_selectors:
            vacancy_cards = soup.select(selector)
            if vacancy_cards:
                print(f"✅ Found {len(vacancy_cards)} cards with selector: {selector}")
                break

        if not vacancy_cards:
            print("❌ No vacancy cards found with any selector")
            # Сохраняем HTML для отладки
            with open('avito_debug.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            print("💾 Saved HTML to avito_debug.html for analysis")
            return []

        # Парсим первые несколько карточек
        for i, card in enumerate(vacancy_cards[:5]):  # ограничиваем для теста
            try:
                vacancy_info = self.parse_vacancy_card(card)
                if vacancy_info:
                    vacancies_data.append(vacancy_info)
                    print(f"📝 Parsed vacancy {i + 1}: {vacancy_info.get('title', 'No title')}")
            except Exception as e:
                print(f"❌ Error parsing card {i + 1}: {e}")
                continue

        return vacancies_data

    def parse_vacancy_card(self, card):
        """Парсит карточку вакансии с Avito"""
        try:
            # Извлекаем заголовок
            title_elem = card.find(['h3', 'a'], class_=lambda x: x and ('title' in x.lower() or 'link' in x.lower()))
            title = title_elem.get_text(strip=True) if title_elem else "No title"

            # Извлекаем ссылку
            link_elem = card.find('a', href=True)
            link = link_elem['href'] if link_elem else ""
            if link and not link.startswith('http'):
                link = self.base_url + link

            # Извлекаем зарплату (если есть)
            salary_elem = card.find(['span', 'meta'],
                                    class_=lambda x: x and ('price' in x.lower() or 'salary' in x.lower()))
            salary = salary_elem.get_text(strip=True) if salary_elem else "Not specified"

            # Извлекаем компанию
            company_elem = card.find(['div', 'span'],
                                     class_=lambda x: x and ('company' in x.lower() or 'firm' in x.lower()))
            company = company_elem.get_text(strip=True) if company_elem else "Not specified"

            return {
                'title': title,
                'link': link,
                'salary': salary,
                'company': company,
                'source': 'Avito'
            }

        except Exception as e:
            print(f"Error parsing vacancy card: {e}")
            return None


if __name__ == "__main__":
    parser = AvitoRabota()

    # Тестируем с разными параметрами
    test_params = {
        'keywords': 'Бухгалтер',
        'area': 'москва',
        'period': 'month',
        'volume': 1
    }

    result = parser.parse_vacantions(test_params)
    print(f"\n🎉 Final result: {len(result)} vacancies found")
    for vacancy in result:
        print(f" - {vacancy}")