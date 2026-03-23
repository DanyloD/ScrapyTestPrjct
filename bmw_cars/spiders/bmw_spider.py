import scrapy
from scrapy_playwright.page import PageMethod


class BmwSpider(scrapy.Spider):
    name = "bmw_used"
    
    custom_settings = {
        'MAX_PAGES': 5
    }

    async def start(self):
        url = "https://usedcars.bmw.co.uk/result/?payment_type=cash&size=23&source=home"

        yield scrapy.Request(
            url,
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", "div.uvl-c-advert", timeout=60000),
                ],
                "current_page": 1
            },
        )

    def parse(self, response):
        current_page = response.meta.get('current_page', 1)
        adverts = response.css('div.uvl-c-advert')
        self.logger.info(f"Page {current_page}: Found {len(adverts)} adverts")

        for advert in adverts:
            details_link = advert.css('a[aria-label^="View details for"]::attr(href)').get()

            if details_link:
                yield response.follow(
                    details_link,
                    callback=self.parse_car_details,
                    meta={
                        "playwright": True,
                        "playwright_page_methods": [
                            PageMethod("wait_for_selector", "p.uvl-c-vehicle-identifier__model", timeout=20000),
                        ],
                    }
                )

        max_pages = self.settings.getint('MAX_PAGES', 5)
        if current_page < max_pages:
            next_page_link = response.css('a[aria-label="Next page"]::attr(href), a.uvl-c-pagination__next::attr(href), li.next a::attr(href)').get()
            
            if not next_page_link:
                 import urllib.parse as urlparse
                 from urllib.parse import urlencode

                 url_parts = list(urlparse.urlparse(response.url))
                 query = dict(urlparse.parse_qsl(url_parts[4]))
                 
                 next_page_num = current_page + 1
                 size = int(query.get('size', 23))
                 
                 query['page'] = str(next_page_num)
                 query['offset'] = str((next_page_num - 1) * size)
                 
                 url_parts[4] = urlencode(query)
                 next_page_link = urlparse.urlunparse(url_parts)
                 self.logger.info(f"Generated next page URL with offset: {next_page_link}")

            if next_page_link:
                next_page_num = current_page + 1
                self.logger.info(f"Moving to next page: {next_page_num} -> {next_page_link}")
                
                next_page_url = response.urljoin(next_page_link)

                yield scrapy.Request(
                    next_page_url,
                    callback=self.parse,
                    dont_filter=True,
                    meta={
                        "playwright": True,
                        "playwright_page_methods": [
                            PageMethod("wait_for_selector", "div.uvl-c-advert", timeout=60000),
                        ],
                        "current_page": next_page_num
                    }
                )


    def parse_car_details(self, response):
        self.logger.info(f"Processing car details: {response.url}")

        model = response.css('p.uvl-c-vehicle-identifier__model::text').get(default='')
        name = response.css('h1.uvl-c-vehicle-identifier__title::text').get(default='')

        car_data = {
            "model": model.strip() if model else "N/A",
            "name": name.strip() if name else "N/A",
            "mileage": "N/A",
            "registered": "N/A",
            "engine": "N/A",
            "range": "N/A",
            "exterior": "N/A",
            "fuel": "N/A",
            "transmission": "N/A",
            "registration": "N/A",
            "upholstery": "N/A",
        }

        spec_titles = response.css('div.uvl-c-specification-overview__title')

        for title_node in spec_titles:
            label = title_node.css('span::text').get(default='').strip().lower()
            
            value_texts = title_node.xpath('./following-sibling::div[contains(@class, "uvl-c-specification-overview__value")]//text()').getall()
            
            value = " ".join([v.strip() for v in value_texts if v.strip()])
            
            if not label or not value:
                continue

            if 'mileage' in label:
                car_data['mileage'] = value
            elif 'registered' in label or 'registration date' in label:
                car_data['registered'] = value
            elif 'engine' in label:
                car_data['engine'] = value
            elif 'range' in label:
                car_data['range'] = value
            elif 'exterior' in label or 'colour' in label:
                car_data['exterior'] = value
            elif 'fuel' in label:
                car_data['fuel'] = value
            elif 'transmission' in label:
                car_data['transmission'] = value
            elif 'registration' in label or 'plate' in label:
                if 'date' not in label:
                    car_data['registration'] = value
            elif 'upholstery' in label or 'interior' in label:
                car_data['upholstery'] = value

        yield car_data
