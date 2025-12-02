import datetime
from bs4 import BeautifulSoup
import time
import random
from parser_programm.Base_Parser import BaseParser


class RabotaRU(BaseParser):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.rabota.ru/"
        self.search_url = "rabota.ru/vacancy"
        self.TOWN_PREFIXES = {
            "москва": "www",
            "санкт-петербург": "spb",
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

    def parse_vacantions(self, search_params):
        time.sleep(random.uniform(3, 7))

        params = {
            'query': search_params.get('keywords', ''),
            'location': search_params.get('area'),
            'period': search_params.get('period', '30'),
            'page': search_params.get('volume'),
        }

        self.town_url = f"https://{self.TOWN_PREFIXES[search_params.get('area').lower()]}.{self.search_url}"

        print(self.town_url)
        response = self.get_response('GET', self.town_url, params=params)

        if response is None:
            print("Не удалось получить ответ от сервера")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        vacancies_data = []

        vacancy_cards = soup.find_all('div', class_='r-serp__item r-serp__item_vacancy')
        print(f"Найдено карточек: {len(vacancy_cards)}")


        for card in vacancy_cards:
            if len(vacancies_data) >= search_params.get('volume'):
                break
            detailed_vacancy = self.detail_data_vacation(card)
            if detailed_vacancy:
                vacancies_data.append(detailed_vacancy)

        return vacancies_data

    def detail_data_vacation(self, card):
        title_elem = card.find('h3', class_='vacancy-preview-card__title')
        title = title_elem.get_text(strip=True) if title_elem else "Не указано"

        link_elem = title_elem.find('a') if title_elem else None
        link = link_elem.get('href', '') if link_elem else ''
        if link and not link.startswith('http'):
            link = f"https://www.rabota.ru{link}"

        salary_elem = card.find('div', class_='vacancy-preview-card__salary')
        salary_text = salary_elem.get_text(strip=True) if salary_elem else 'Нет информации по зарплате'

        salary_middle = self.parse_salary(salary_text)

        company_elem = card.find('span', class_='vacancy-preview-card__company-name')
        company = company_elem.get_text(strip=True) if company_elem else "Не указано"

        address_elem = card.find('span', class_='vacancy-preview-location__address-text')
        address = address_elem.get_text(strip=True) if address_elem else 'Нет информации о адресе'

        date_elem = card.find('meta', itemprop='datePosted')
        published_at = date_elem.get('content', '') if date_elem else ''

        experience = "Не указано"
        employment = "Не указано"
        schedule = "Не указано"


        if link:
            response2 = self.get_response('GET', link)
            if response2:
                soup2 = BeautifulSoup(response2.text, 'html.parser')
                detail_vacancy_card = soup2.find('div', class_='vacancy-card__main')

                if detail_vacancy_card:
                    schedule_text = ""

                    requirements_elem = detail_vacancy_card.find('div', class_='vacancy-requirements')
                    if requirements_elem:
                        requirements_text = requirements_elem.get_text(strip=True)
                        schedule_text += requirements_text + " "

                        if ',' in requirements_text:
                            try:
                                experience_part = requirements_text.split(',', 1)[1].strip()
                                experience = experience_part
                            except:
                                experience = requirements_text
                        else:
                            experience = requirements_text


                    full_desc_elem = detail_vacancy_card.find('div', itemprop='description')
                    if full_desc_elem:
                        full_description = full_desc_elem.get_text(strip=True)
                        schedule_text += full_description + " "

                    conditions_elem = detail_vacancy_card.find('div', class_='vacancy-conditions')
                    if conditions_elem:
                        conditions_text = conditions_elem.get_text(strip=True)
                        schedule_text += conditions_text + " "

                    schedule = self.extract_schedule(schedule_text)

                    employment_elem = detail_vacancy_card.find('meta', itemprop='employmentType')
                    if employment_elem:
                        employment = employment_elem.get('content', 'Не указано')

                    detail_address_elem = detail_vacancy_card.find('div', class_='vacancy-locations__address')
                    if detail_address_elem:
                        address = detail_address_elem.get_text(strip=True)

        if published_at:
            try:
                dt = datetime.datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                formatted_date = dt.strftime("%d.%m.%Y %H:%M")
            except:
                formatted_date = "Не указана"
        else:
            formatted_date = "Не указана"

        self.processed_vacancy = {
            'agregator': 'Rabota.ru',
            'name': title,
            'company': company,
            'salary': salary_middle,
            'address': address,
            'experience': self.extract_experience(experience),
            'employment': 'Полная занятость' if employment == 'полный рабочий день' else 'Не имеет значения',
            'schedule': schedule,
            'url': link,
            'published_at': formatted_date,
        }

        return self.processed_vacancy

    def parse_salary(self, salary_text):
        if not salary_text:
            return None

        numbers = []
        for word in salary_text.split():

            clean_word = ''.join(filter(str.isdigit, word))
            if clean_word:
                numbers.append(int(clean_word))

        if len(numbers) == 2:
            return f"в среднем {(numbers[0] + numbers[1]) // 2} рублей"
        elif numbers:
            return f"от {numbers[0]} рублей"
        else:
            return 'Не указана'

    def parse_salary(self, salary_text):
        if not salary_text:
            return None

        numbers = []
        for word in salary_text.split():
            if word.isdigit():
                if int(word) != 0:
                    numbers.append(int(word) * 1000)

        if len(numbers) == 2:
            return f"в среднем {(numbers[0] + numbers[1]) // 2} рублей"
        elif numbers:
            return f"от {numbers[0]} рублей"
        else:
            return 'Не указана'


    def extract_experience(self, requirement_text):

        experience, education = requirement_text.split(',')

        if not requirement_text:
            return "Не имеет значения"

        if experience == "опыт работы от 1 года":
            return "От 1 года" + ", " + education
        if experience == "опыт работы от 3 лет":
            return "От 3 лет" + ", " + education
        if experience == "опыт работы не имеет значения":
            return "Нет опыта" + ", " + education

        return "Не имеет значения"

    def extract_schedule(self, text):
        if not text:
            return "Не указано"

        text_lower = text.lower()


        if '5/2' in text_lower or '5/2.' in text_lower or '5/2,' in text_lower:
            return '5/2'
        elif '2/2' in text_lower or '2/2.' in text_lower or '2/2,' in text_lower:
            return '2/2'
        elif '15/15' in text_lower or '15/15.' in text_lower or '15/15,' in text_lower:
            return '15/15'
        elif '20/10' in text_lower or '20/10.' in text_lower or '20/10,' in text_lower:
            return '20/10'


        return "Не указано"




"""if __name__ == "__main__":
    r = RabotaRU()
    result = r.parse_vacantions({
        'keywords': 'Бухгалтер',
        'area': 'Москва',
        'period': 1,
        'page': 3
    })
    print("Результаты парсинга:")
    for i, vac in enumerate(result, 1):
        print(f"\n{i}. {vac.get('name', 'Нет названия')}")
        print(f"   Компания: {vac.get('company', 'Не указана')}")
        print(f"   Зарплата: {vac.get('salary', 'Не указана')}")
        print(f"   Адрес: {vac.get('address', 'Не указан')}")
        print(f"   Опыт: {vac.get('experience', 'Не указан')}")
        print(f"   Занятость: {vac.get('employment', 'Не указана')}")
        print(f"   График: {vac.get('schedule', 'Не указан')}")
        print(f"   Ссылка: {vac.get('url', 'Нет ссылки')}")
        print(f"   Дата: {vac.get('published_at', 'Не указана')}")"""