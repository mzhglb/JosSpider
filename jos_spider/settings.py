# Scrapy settings for jos_spider project

BOT_NAME = 'jos_spider'

SPIDER_MODULES = ['jos_spider.spiders']
NEWSPIDER_MODULE = 'jos_spider.spiders'

# 搜索条件配置
# 如果不需要使用搜索条件，将对应的值设置为空字符串
SEARCH_KEY1 = '软件工程'  # 第一个搜索框的内容
SEARCH_KEY2 = ''  # 第二个搜索框的内容

# 请求头随机化中间件
DOWNLOADER_MIDDLEWARES = {
    'jos_spider.middlewares.RandomUserAgentMiddleware': 400,
    'jos_spider.middlewares.SeleniumMiddleware': 543,
}

# 启用数据处理管道
ITEM_PIPELINES = {
    'jos_spider.pipelines.JosSpiderPipeline': 300,
}

# 遵守robots.txt规则
ROBOTS_TXT_OBEY = True

# 并发请求数
CONCURRENT_REQUESTS = 16

# 对同一网站的并发请求数
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# 下载延迟（秒）
DOWNLOAD_DELAY = 3

# 随机化下载延迟
RANDOMIZE_DOWNLOAD_DELAY = True

# 默认请求头
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 输出设置
FEEDS = {
    'jos_articles.json': {
        'format': 'json',
        'encoding': 'utf-8',
        'indent': 2,
        'overwrite': True
    }
}

# Selenium设置
SELENIUM_DRIVER_NAME = 'chrome'
SELENIUM_DRIVER_EXECUTABLE_PATH = None  # 自动下载
SELENIUM_DRIVER_ARGUMENTS = [
    '--headless=new',  # 使用新版无头模式
    '--disable-gpu',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--log-level=3',  # 减少日志输出
    '--disable-logging',  # 禁用日志
    '--ignore-certificate-errors',  # 忽略证书错误
    '--disable-extensions',  # 禁用扩展
    '--disable-software-rasterizer',  # 禁用软件光栅化
    '--disable-notifications',  # 禁用通知
    '--window-size=1920,1080',  # 设置窗口大小
    '--start-maximized',  # 最大化窗口
    '--disable-blink-features=AutomationControlled'  # 禁用自动化检测
]  # 优化的无头模式配置

# Selenium等待设置（所有时间单位均为秒）
# 页面加载超时时间，控制页面整体加载的最大等待时间
SELENIUM_PAGE_LOAD_TIMEOUT = 60

# 脚本执行超时时间，控制JavaScript脚本执行的最大等待时间
SELENIUM_SCRIPT_TIMEOUT = 60

# 元素定位超时时间，控制查找单个元素的最大等待时间
SELENIUM_ELEMENT_TIMEOUT = 15

# 页面内容渲染等待时间，确保页面有足够内容加载完成
SELENIUM_CONTENT_RENDER_TIMEOUT = 30

# 搜索结果加载等待时间，点击搜索按钮后等待结果加载的时间
SELENIUM_SEARCH_RESULT_WAIT = 5

# 重试间隔时间，每次重试前的等待时间
SELENIUM_RETRY_INTERVAL = 2

# 重试设置
RETRY_ENABLED = True
RETRY_TIMES = 1
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# 超时设置
DOWNLOAD_TIMEOUT = 30