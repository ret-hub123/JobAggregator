import datetime
from bs4 import BeautifulSoup
import time
import random
from parser_programm.BaseParser import BaseParser


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

        company_elem = card.find('span', class_='vacancy-preview-card__company-name')
        company = company_elem.get_text(strip=True) if company_elem else "Не указано"

        address_elem = card.find('span', class_='vacancy-preview-location__address-text')
        address = address_elem.get_text(strip=True) if address_elem else 'Нет информации о адресе'

        description_elem = card.find('div', class_='vacancy-preview-card__short-description')
        description = description_elem.get_text(strip=True) if description_elem else ''

        date_elem = card.find('meta', itemprop='datePosted')
        published_at = date_elem.get('content', '') if date_elem else ''

        experience = "Не указано"
        employment = "Не указано"
        schedule = "Не указано"
        full_description = description

        if link:
            response2 = self.get_response('GET', link)
            if response2:
                soup2 = BeautifulSoup(response2.text, 'html.parser')
                detail_vacancy_card = soup2.find('div', class_='vacancy-card__main')

                if detail_vacancy_card:

                    requirements_elem = detail_vacancy_card.find('div', class_='vacancy-requirements')
                    if requirements_elem:
                        requirements_text = requirements_elem.get_text(strip=True)

                        if ',' in requirements_text:
                            experience_part = requirements_text.split(',', 1)[1].strip()
                            experience = experience_part
                        else:
                            experience = requirements_text

                    employment_elem = detail_vacancy_card.find('meta', itemprop='employmentType')
                    if employment_elem:
                        employment = employment_elem.get('content', 'Не указано')


                    full_desc_elem = detail_vacancy_card.find('div', itemprop='description')
                    if full_desc_elem:
                        full_description = full_desc_elem.get_text(strip=True)


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
            'salary': salary_text,
            'address': address,
            'experience': experience,
            'employment': employment,
            'schedule': schedule,
            'url': link,
            'published_at': formatted_date,
            'description': full_description
        }


        return self.processed_vacancy




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