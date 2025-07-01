BOT_NAME = "scrapy_project"
SPIDER_MODULES = ["osint.scrapy_project"]
NEWSPIDER_MODULE = "osint.scrapy_project"
ITEM_PIPELINES = {"osint.scrapy_project.pipelines.ImagePipeline": 300}
ROBOTSTXT_OBEY = True
