from scrapy import signals
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import time

class RandomUserAgentMiddleware:
    def __init__(self):
        self.ua = UserAgent()

    def process_request(self, request, spider):
        request.headers['User-Agent'] = self.ua.random

class SeleniumMiddleware:
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 添加自定义 User-Agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 添加更多的反自动化检测绕过
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                window.chrome = {
                    runtime: {}
                };
            '''
        })

    def process_request(self, request, spider):
        if 'advanced_search' in request.url:
            max_retries = spider.settings.getint('RETRY_TIMES', 3)  # 增加重试次数
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    spider.logger.info(f'正在尝试加载页面，第 {retry_count + 1} 次尝试')
                    
                    # 清除所有 cookies
                    self.driver.delete_all_cookies()
                    
                    # 设置页面加载策略
                    self.driver.set_page_load_timeout(spider.settings.getint('SELENIUM_PAGE_LOAD_TIMEOUT'))  # 页面加载超时时间
                    self.driver.set_script_timeout(spider.settings.getint('SELENIUM_SCRIPT_TIMEOUT'))       # 脚本执行超时时间
                    
                    self.driver.get(request.url)
                    
                    # 等待页面加载完成的多重检查
                    WebDriverWait(self.driver, spider.settings.getint('SELENIUM_PAGE_LOAD_TIMEOUT')).until(
                        lambda driver: driver.execute_script('return document.readyState') == 'complete'
                    )
                    spider.logger.info('页面基础加载完成，等待内容渲染')
                    
                    # 检查页面是否有实际内容
                    WebDriverWait(self.driver, spider.settings.getint('SELENIUM_CONTENT_RENDER_TIMEOUT')).until(
                        lambda driver: len(driver.find_elements(By.TAG_NAME, 'body')[0].text.strip()) > 100  # 确保页面有足够的内容
                    )
                    spider.logger.info('页面内容已渲染')
                    
                    # 检查页面URL是否正确
                    current_url = self.driver.current_url
                    if 'data:,' in current_url or current_url == 'about:blank':
                        raise Exception(f'页面加载失败，URL不正确: {current_url}')
                    spider.logger.info('URL验证通过')
                        
                    # 检查页面标题
                    WebDriverWait(self.driver, spider.settings.getint('SELENIUM_ELEMENT_TIMEOUT')).until(
                        lambda driver: bool(driver.title.strip())
                    )
                    spider.logger.info('页面标题加载完成')
                    
                    # 尝试多种定位方式
                    selectors = [
                        (By.CSS_SELECTOR, '[onclick="SearchData(1);"]'),
                        (By.XPATH, "//button[@onclick='SearchData(1);']"),
                        (By.CSS_SELECTOR, '.search-btn'),
                        (By.XPATH, "//button[contains(@class, 'search-btn')]"),
                    ]
                    
                    search_button = None
                    for by, selector in selectors:
                        try:
                            spider.logger.info(f'尝试使用选择器: {selector}')
                            search_button = WebDriverWait(self.driver, spider.settings.getint('SELENIUM_ELEMENT_TIMEOUT')).until(
                                EC.element_to_be_clickable((by, selector))
                            )
                            if search_button:
                                break
                        except Exception as e:
                            spider.logger.debug(f'使用选择器 {selector} 未找到元素: {str(e)}')
                            continue
                    
                    if not search_button:
                        raise Exception('无法找到查询按钮')
                    
                    # 确保元素可见且可点击
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
                    time.sleep(1)
                    search_button.click()
                    
                    # 等待搜索结果加载（单位：秒）
                    time.sleep(spider.settings.getint('SELENIUM_SEARCH_RESULT_WAIT'))
                    
                    # 获取页面内容
                    body = self.driver.page_source
                    spider.logger.info('页面内容获取成功')
                    return scrapy.http.HtmlResponse(
                        url=request.url,
                        body=body.encode('utf-8'),
                        encoding='utf-8',
                        request=request
                    )
                    
                except Exception as e:
                    retry_count += 1
                    spider.logger.error(f'第 {retry_count} 次尝试失败: {str(e)}')
                    if retry_count >= max_retries:
                        spider.logger.error('达到最大重试次数，放弃处理')
                        return None
                    time.sleep(spider.settings.getint('SELENIUM_RETRY_INTERVAL'))  # 重试前等待（单位：秒）

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_closed, signals.spider_closed)
        return middleware

    def spider_closed(self):
        self.driver.quit()