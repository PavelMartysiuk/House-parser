import requests
from requests import HTTPError
from sqlalchemy.exc import IntegrityError
from bs4 import BeautifulSoup
import tables


class ParseBlagovist:
    """Parse advertisements from https://blagovist.ua"""

    def __init__(self):
        self.url = 'https://blagovist.ua/search/house/sale/sd_21710/cur_3/kch_1'
        self.advertisements_links = []

    def check_connect(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
        except HTTPError as httperr:
            print(f'HttpError: {httperr}')
            self.response = None
        except Exception as exc:
            print(f'Exception: {exc}')
            self.response = None
        else:
            self.response = response.text

    def conversion_to_soup(self):
        self.soup = BeautifulSoup(self.response, 'html.parser')

    def validate_house(self, area, cost):
        MAX_AREA = 200
        MAX_COST = 80000
        if area <= MAX_AREA and cost <= MAX_COST:
            self.validate_status = True
        else:
            self.validate_status = False

    def save_in_bd(self, link, cost, area, location):
        sess = tables.Session()
        new_row = tables.House(link=link, cost=cost, area=area, location=location)
        try:
            sess.add(new_row)
            sess.flush()
        except IntegrityError:
            self.replay_advertisement = True  # reply link in bd
        else:
            sess.commit()
            self.replay_advertisement = False

    def get_quantity_pages(self):
        self.check_connect(self.url)
        PAGES_LINKS_BLOK_INDEX = 1
        if self.response:
            self.conversion_to_soup()
            pages_links_block = self.soup.find_all('ul', class_='pager__items js-pager__items')[PAGES_LINKS_BLOK_INDEX]
            self.pages_links = [page.find('a').get('href') for page in pages_links_block.find_all('li')]

    def parse_advertisements_links(self):
        self.get_quantity_pages()
        for link in self.pages_links:
            self.check_connect(link)
            if self.response:
                self.conversion_to_soup()
                advertisements_blocks = self.soup.find_all('div', class_='col-md-11')
                advertisements_links = [block.find('a').get('href') for block in advertisements_blocks]
                self.advertisements_links.extend(advertisements_links)

    def parse_advertisements(self):
        self.parse_advertisements_links()
        HOUSE_PARAMATRS_BLOCK_INDEX = 1
        END_COST = -1  # last symbol $( example 255 000 $ )
        for link in self.advertisements_links:
            self.check_connect(link)
            if self.response:
                self.conversion_to_soup()
                cost = self.soup.find('div', 'm-dollar').find('b').text[:END_COST].strip()
                cost = float(''.join(cost.split()))  # bad format for int(example 255 000)
                house_info_block = self.soup.find_all('ul', class_='list-unstyled')[HOUSE_PARAMATRS_BLOCK_INDEX]
                house_info_block = house_info_block.find_all('li')
                for element in house_info_block:
                    parameter = element.find('em').text.strip()
                    if parameter == 'Расположение':
                        self.location = element.find('span').text.strip()
                    elif parameter == 'Общая площадь':
                        self.area = float(element.find('span').text.strip())
                self.validate_house(area=self.area, cost=cost)
                if self.validate_status:
                    self.save_in_bd(link, cost, self.area, self.location)
                    if self.replay_advertisement:
                        print('I have this record in bd')
                        break


class ParseRelty(ParseBlagovist):
    """Parse https://100realty.ua/realty_search/house/sale/sd_20001/p__80000/cur_4/kch_1"""

    def __init__(self):
        """Parse https://100realty.ua/realty_search/house/sale/sd_20001/p__80000/cur_4/kch_1"""
        self.url = 'https://100realty.ua/realty_search/house/sale/sd_20001/p__80000/cur_4/kch_1'

    def get_quantity_pages(self):
        self.check_connect(self.url)
        if self.response:
            self.conversion_to_soup()
            paginator_block = self.soup.find('ul', class_='pager__items js-pager__items')
            pages_links_block = paginator_block.find_all('a')
            self.pages_links = {link.get('href') for link in pages_links_block}  # delete current link

    def parse_advertisements(self):
        SITE_URL = 'https://100realty.ua'
        END_COST = 2
        self.get_quantity_pages()
        for link in self.pages_links:
            self.check_connect(link)
            if self.response:
                self.conversion_to_soup()
                advertisements_blocks = self.soup.find_all('div', class_='object-additional-info-wrapper')
                for advertisement_block in advertisements_blocks:
                    location = advertisement_block.find('a').text
                    link = SITE_URL + advertisement_block.find('a').get('href')
                    area = float(advertisement_block.find('div', class_='object-square object-info-item'). \
                                 find('div', class_='value').text)
                    cost = advertisement_block.find('div', class_='cost-field'). \
                        find('div', class_='usd-price-value').text
                    cost = float(''.join(cost.split()[:END_COST]))
                    self.save_in_bd(link=link, cost=cost, area=area, location=location)
                    if self.replay_advertisement:
                        print('I have this record in bd')
                        break


class ParseCountry(ParseBlagovist):
    """Paarse 'https://www.country.ua/list/?action_id=1&action_url=buy&type_id=2&type_url=house&rooms_id=&rooms_url=&filter_flat_type_id=&filter_flat_type_url=&price_currency=usd&price_from=&price_to=80000&price_id=&price_url=&metro=&metro_id=&metro_url=&rayon=&rayon_id=&rayon_url=&sub_id=87&sub_url=svyatoshin&location=&location_id=87&location_type=sub&location_url=svyatoshin&object_id=&phone=&filter_time_id=&filter_time_url=&size_1_from=&size_1_to=&size_1_id=&size_1_url=&size_2_from=&size_2_to=&size_2_id=&size_2_url=&size_3_from=&size_3_to=&size_3_id=&size_3_url=&floor_from=&floor_to=&floor_id=&floor_url=&floors_from=&floors_to=&floors_id=&floors_url=&city_id=29586&lang=ru&price_sort=default'"""

    def __init__(self):
        self.url = 'https://www.country.ua/list/?action_id=1&action_url=buy&type_id=2&type_url=house&rooms_id=&rooms_url=&filter_flat_type_id=&filter_flat_type_url=&price_currency=usd&price_from=&price_to=80000&price_id=&price_url=&metro=&metro_id=&metro_url=&rayon=&rayon_id=&rayon_url=&sub_id=87&sub_url=svyatoshin&location=&location_id=87&location_type=sub&location_url=svyatoshin&object_id=&phone=&filter_time_id=&filter_time_url=&size_1_from=&size_1_to=&size_1_id=&size_1_url=&size_2_from=&size_2_to=&size_2_id=&size_2_url=&size_3_from=&size_3_to=&size_3_id=&size_3_url=&floor_from=&floor_to=&floor_id=&floor_url=&floors_from=&floors_to=&floors_id=&floors_url=&city_id=29586&lang=ru&price_sort=default'

    def parse_advertisements(self):
        AREA_INDEX = 1
        COST_INDEX = 0
        self.check_connect(self.url)
        if self.response:
            self.conversion_to_soup()
            advertisements_blocks = self.soup.find_all('div', class_='item-catalog__body')
            for advertisement in advertisements_blocks:
                location = advertisement.find('div', class_='item-catalog__address address').text
                area_block = advertisement.find('div', class_='item-catalog__size').text
                area = float(area_block.split()[AREA_INDEX])
                cost = advertisement.find('div', class_='item-catalog__price').text  # cost in format 200 $
                cost = float(cost.split()[COST_INDEX])
                link = f'{self.url}  {location}'  # I make unique url. Advertisement  doesn't have own url. Column link is unique in bd.
                self.save_in_bd(link=link, cost=cost, location=location, area=area)
                if self.replay_advertisement:
                    print('I have this record in bd')
                    break


class ParseMeget(ParseBlagovist):
    """Parse https://meget.kiev.ua/prodazha-domov/?offer_geo_id=3&offer_geo_id_dict1=2&offer_geo_id_dict2=3&price_from=&price_to=80000&offer_currency=USD&offer_category_id=40&offer_sost=&area_from=&area_to=200&living_from=&living_to=&offer_period=90&offer_id="""

    def __init__(self):
        self.url = 'https://meget.kiev.ua/prodazha-domov/?offer_geo_id=3&offer_geo_id_dict1=2&offer_geo_id_dict2=3&price_from=&price_to=80000&offer_currency=USD&offer_category_id=40&offer_sost=&area_from=&area_to=200&living_from=&living_to=&offer_period=90&offer_id='
        self.advertisements_info = {}
        self.SITE = 'https://meget.kiev.ua/'

    def get_pages_links(self):
        self.check_connect(self.url)
        if self.response:
            self.conversion_to_soup()
            pages_block = self.soup.find('div', class_='pages')
            pages_links = pages_block.find_all('a', rel='nofollow')
            self.pages_links = [self.SITE + link.get('href') for link in pages_links]  # not curr page in paginator
            self.pages_links.append(self.url)

    def get_advertisements_links(self):
        AREA_BLOCK_INDEX = 2
        AREA_INDEX = 1
        self.get_pages_links()
        for page_link in self.pages_links:
            self.check_connect(page_link)
            if self.response:
                self.conversion_to_soup()
                advertisements_blocks = self.soup.find_all('div', class_='offer-block-wrap out-link offer-simple')
                for advertisement_block in advertisements_blocks:
                    advertisement_link = self.SITE + advertisement_block.find('a', class_='offer-link-block').get(
                        'href')
                    house_info = advertisement_block.find('span', class_='offer-description-text').find_all('span')
                    area = house_info[AREA_BLOCK_INDEX].text  # format is Площадь: 63 м
                    area = float(area.split()[AREA_INDEX])
                    self.advertisements_info[advertisement_link] = area

    def get_advertisements_info(self):
        COST_INDEX = 4
        self.get_advertisements_links()
        for advertisement_link in self.advertisements_info.keys():  # format{link:area}. Advertisement doesn't have a area in the form
            self.check_connect(advertisement_link)
            if self.response:
                self.conversion_to_soup()
                advertisements_info_block = self.soup.find('div', class_='detail-page-top-new')
                location = advertisements_info_block.find('h2').text
                cost = self.soup.find('p',
                                      class_='price-about').text  # <p class="price-about">цена всего объекта:<br> $ 52500 / &euro; 48387</p>
                cost = float(cost.split()[COST_INDEX])
                self.save_in_bd(link=advertisement_link, cost=cost, location=location,
                                area=self.advertisements_info[
                                    advertisement_link])  # self.advertisements_info = {link:area}
                if self.replay_advertisement:
                    print('I have this record in bd')
                    break


class ParseBn(ParseBlagovist):
    """Parse advertisements from https://bn.ua/find/?optype=1&topic_id=5&region_id=5&srch_word=&city_id%5B%5D=11&currency_id=2&price_min=&price=80000&search=&floor_count_min=&square_min=&square_max=&live_square_min=&live_square_max=&kitchen_square_min=&kitchen_square_max=&land_area_min=&land_area_max=&id=&phone=&grid_type=thumbs&grid_type=thumbs"""

    def __init__(self):
        self.url = 'https://bn.ua/find/?optype=1&topic_id=5&region_id=5&srch_word=&city_id%5B%5D=11&currency_id=2&price_min=&price=80000&search=&floor_count_min=&square_min=&square_max=&live_square_min=&live_square_max=&kitchen_square_min=&kitchen_square_max=&land_area_min=&land_area_max=&id=&phone=&grid_type=thumbs&grid_type=thumbs'
        self.SITE = 'https://bn.ua'

    def get_advertisements(self):
        END_COST = -1  # last symbol $
        AREA_INDEX = 2
        self.check_connect(self.url)
        if self.response:
            self.conversion_to_soup()
            advertisements_blocks = self.soup.find_all('div', class_='col-md-12 col-sm-12')
            for advertisement_block in advertisements_blocks:
                location = advertisement_block.find('a', class_='ellipsed').text.strip()
                link = self.SITE + advertisement_block.find('a', class_='ellipsed').get('href')
                cost_block = advertisement_block.find('div', class_='col-md-4 col-sm-4 col-xs-3 price-float')
                cost = cost_block.find('a').text.split()  # format is 80  000 $
                cost = float(''.join(cost[:END_COST]))
                area = advertisement_block.find('div',
                                                class_='col-md-9 col-sm-9 col-xs-9').text  # format is 4-комн., площадь 190 м2, 4 сот., этажей 2
                area = float(area.split()[AREA_INDEX])
                self.save_in_bd(link=link, cost=cost, location=location, area=area)
                if self.replay_advertisement:
                    print('I have this record in bd')
                    break


class ParseRieltor(ParseBlagovist):
    """Parse """

    def __init__(self):
        self.url = 'https://rieltor.ua/houses-sale/Святошинский-d86/?currency=2&price_max=80000&common_area_max=200'
        self.SITE = 'https://rieltor.ua'

    def parse_advertisements(self):
        self.check_connect(self.url)
        END_COST = -1
        if self.response:
            self.conversion_to_soup()
            advertisements_blocks = self.soup.find_all('div', class_='catalog-item')
            for advertisement_block in advertisements_blocks:
                link = self.SITE + advertisement_block.find('h2', class_='catalog-item__title').find('a').get('href')
                location = advertisement_block.find('h2', class_='catalog-item__title').find('a').text
                area_block = advertisement_block.find('div',
                                                      class_='catalog-item_info-item-row').text.strip()  # format is 3 поверху, таунхаус  77 / 48 / 20 м²
                split_area = area_block.split()
                area = sum([float(area) for area in split_area if area.isdigit()])
                cost = advertisement_block.find('strong', class_='catalog-item__price').text  # soct in format 50 000 $
                cost = float(''.join(cost.split()[:END_COST]))
                self.save_in_bd(link=link, location=location, area=area, cost=cost)
                if self.replay_advertisement:
                    print('I have this record in bd')
                    break


class ParseProstodom(ParseBlagovist):
    """Parse https://prostodom.ua/prodam_dom_svyatoshinskiy?priceMax=80000&squareMax=200"""

    def __init__(self):
        self.url = 'https://prostodom.ua/prodam_dom_svyatoshinskiy?priceMax=80000&squareMax=200'
        self.SITE = 'https://prostodom.ua'

    def parse_advertisements(self):
        AREA_INDEX = 1
        self.check_connect(self.url)
        if self.response:
            self.conversion_to_soup()
            advertisements_blocks = self.soup.find_all('div', class_='row box-row')
            for advertisement_block in advertisements_blocks:
                link = self.SITE + advertisement_block.find('a').get('href')
                location = advertisement_block.find('a').get('title')
                str_cost = advertisement_block.find('h5', class_='d-inline-block classicH').text  # format is 80,000 $
                cost = float(''.join([symbol for symbol in str_cost if symbol.isdigit()]))
                try:
                    area = advertisement_block.find('span', title='Площадь жилая').text  # format is / 150
                    area = area.split()[AREA_INDEX]
                except AttributeError:
                    continue
                self.save_in_bd(link=link, location=location, area=area, cost=cost)
                if self.replay_advertisement:
                    print('I have this record in bd')
                    break


class ParseObyava(ParseBlagovist):
    """Parse https://obyava.ua/ru/nedvizhimost/prodazha-dach/kievo-svyatoshinskiy?priceto=80000&currency=usd"""

    def __init__(self):
        self.url = 'https://obyava.ua/ru/nedvizhimost/prodazha-dach/kievo-svyatoshinskiy?priceto=80000&currency=usd'
        self.advertisements_links = []

    def get_advertisements_links(self):
        self.check_connect(self.url)
        if self.response:
            self.conversion_to_soup()
            advertisements_bloks = self.soup.find_all('div', class_='info-block')
            for advertisement_blok in advertisements_bloks:
                link = advertisement_blok.find('a').get('href')
                self.advertisements_links.append(link)

    def parse_advertisements(self):
        LOCATION_ROW_INDEX = 2
        AREA_ROW_INDEX = 5
        AREA_INDEX = 0
        self.get_advertisements_links()
        for link in self.advertisements_links:
            self.check_connect(link)
            if self.response:
                self.conversion_to_soup()
                advertisements_info_block = self.soup.find('div', class_='col pull-right')
                cost = advertisements_info_block.find('span', class_='tooltip').text  # format is 70 000USD
                cost = float(''.join([sym for sym in cost if sym.isdigit()]))
                location_area_block = advertisements_info_block.find('table', class_='').find_all('tr')
                try:
                    location = location_area_block[LOCATION_ROW_INDEX].find('td').text
                    area = location_area_block[AREA_ROW_INDEX].find('td').text.strip()  # format is 120 м2 обш. пл.
                    area = float(area.split()[AREA_INDEX])
                except IndexError:
                    continue
                self.save_in_bd(link=link, location=location, area=area, cost=cost)
                if self.replay_advertisement:
                    print('I have this record in bd')
                    break


class ParseAddress(ParseBlagovist):
    """https://address.ua/kiev/prodazha-domov-g-svyatoshinskijj/?pricetousd=80000&sortfield=rank"""

    def __init__(self):
        self.url = 'https://address.ua/kiev/prodazha-domov-g-svyatoshinskijj/?pricetousd=80000&sortfield=rank'
        self.links = []

    def get_advertisements_links(self):
        self.check_connect(self.url)
        if self.response:
            self.conversion_to_soup()
            advertisements_blocks = self.soup.find_all('div', class_='item')
            for advertisement_block in advertisements_blocks:
                link = 'https:' + advertisement_block.find('a').get('href')
                self.links.append(link)

    def parse_advertisements(self):
        AREA_INDEX = 1
        self.get_advertisements_links()
        for link in self.links:
            self.check_connect(link)
            if self.response:
                self.conversion_to_soup()
                location = self.soup.find('div', class_='address').text.strip()
                cost = self.soup.find('option', title="$").get('value')  # format is 125 000
                cost = float(''.join(cost.split()))
                advertisement_info = self.soup.find('div', class_='prop-item')
                area = float(advertisement_info.find('span').text.split()[AREA_INDEX])
                self.save_in_bd(link=link, location=location, area=area, cost=cost)
                if self.replay_advertisement:
                    print('I have this record in bd')
                    break


if __name__ == '__main__':
    blagovist = ParseBlagovist()
    blagovist.parse_advertisements()
    relty = ParseRelty()
    relty.parse_advertisements()
    country = ParseCountry()
    country.parse_advertisements()
    merget = ParseMeget()
    merget.get_advertisements_info()
    bn = ParseBn()
    bn.get_advertisements()
    rieltor = ParseRieltor()
    rieltor.parse_advertisements()
    prosto_dom = ParseProstodom()
    prosto_dom.parse_advertisements()
    abyava = ParseObyava()
    abyava.parse_advertisements()
    address = ParseAddress()
    address.parse_advertisements()
