import scrapy


class ImageItem(scrapy.Item):
    user_id = scrapy.Field()
    source_url = scrapy.Field()
    image_url = scrapy.Field()
    image_bytes = scrapy.Field()
