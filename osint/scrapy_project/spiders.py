import scrapy

from .items import ImageItem


class ImageSpider(scrapy.Spider):
    name = "image_spider"

    def start_requests(self):
        urls = getattr(self, "urls", "").split(",")
        for url in urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        for img in response.css("img::attr(src)").getall():
            yield ImageItem(source_url=response.url, image_url=response.urljoin(img))
