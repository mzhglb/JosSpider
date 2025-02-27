import scrapy
from scrapy.http import Request
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
import json
import logging
from typing import Optional, Union, Tuple
import time

class JosSpider(scrapy.Spider):
    name = 'jos'
    allowed_domains = ['jos.org.cn']
    start_urls = ['https://jos.org.cn/jos/article/advanced_search']
    
    def __init__(self):
        super().__init__()
        self.driver = webdriver.Chrome()
        # 增加等待时间到30秒
        self.wait = WebDriverWait(self.driver, 30)
        self.max_retries = 3
        # 添加已访问页面集合用于去重
        self.visited_pages = set()
        # 记录总页数
        self.total_pages = None

    def wait_for_element(self, locator: Tuple[By, str], timeout: int = 30, visible: bool = True) -> Optional[webdriver.remote.webelement.WebElement]:
        """统一的元素等待和定位方法
        
        Args:
            locator: 元素定位器，格式为(By.XXX, 'selector')
            timeout: 超时时间（秒）
            visible: 是否要求元素可见
        
        Returns:
            找到的元素对象，如果未找到则返回None
        """
        try:
            if visible:
                return self.wait.until(EC.visibility_of_element_located(locator))
            return self.wait.until(EC.presence_of_element_located(locator))
        except TimeoutException:
            self.logger.error(f'等待元素超时: {locator}')
            return None

    def safe_click(self, element: webdriver.remote.webelement.WebElement, retry_count: int = 0) -> bool:
        """安全的点击操作，处理各种点击异常
        
        Args:
            element: 要点击的元素
            retry_count: 当前重试次数
        
        Returns:
            点击是否成功
        """
        if retry_count >= self.max_retries:
            self.logger.error('点击操作超过最大重试次数')
            return False

        try:
            if not element.is_enabled():
                self.logger.warning('元素不可点击')
                return False
            
            try:
                element.click()
            except ElementClickInterceptedException:
                # 如果普通点击失败，尝试使用JavaScript点击
                self.driver.execute_script("arguments[0].click();", element)
                
            return True
            
        except Exception as e:
            self.logger.warning(f'点击操作失败: {str(e)}, 正在重试...')
            return self.safe_click(element, retry_count + 1)
    
    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse)
    
    def wait_for_page_load(self, form_id: str = 'article_search_form') -> bool:
        """统一的页面加载等待方法
        
        Args:
            form_id: 用于验证页面加载完成的表单ID
        
        Returns:
            页面是否成功加载
        """
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                # 等待页面完全加载
                self.wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
                self.logger.info('页面基础DOM加载完成')
                
                # 等待页面可见性
                self.wait.until(lambda driver: driver.execute_script('return document.visibilityState') == 'visible')
                self.logger.info('页面可见性状态确认')
                
                # 等待指定表单加载并可见
                if form_id:
                    form = self.wait_for_element((By.ID, form_id))
                    if not form:
                        raise TimeoutException(f'表单 {form_id} 加载失败')
                    self.logger.info(f'表单 {form_id} 加载完成且可见')
                    
                return True
                
            except TimeoutException as e:
                retry_count += 1
                self.logger.warning(f'页面加载重试 {retry_count}/{self.max_retries}: {str(e)}')
                if retry_count >= self.max_retries:
                    self.logger.error('页面加载失败，超过最大重试次数')
                    return False
                self.driver.refresh()
        return False

    def wait_for_article_list_update(self, old_content: str = None) -> bool:
        """等待文章列表更新
        
        Args:
            old_content: 更新前的文章列表内容
            
        Returns:
            是否成功检测到更新
        """
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                # 等待文章列表容器可见
                article_list = self.wait_for_element(
                    (By.ID, 'EtTableArticleList'),
                    timeout=30,
                    visible=True
                )
                if not article_list:
                    raise TimeoutException('文章列表容器未找到')
                
                # 如果提供了旧内容，则验证内容是否更新
                if old_content:
                    new_content = article_list.get_attribute('innerHTML')
                    if new_content != old_content:
                        self.logger.info('文章列表内容已更新')
                        return True
                    
                    retry_count += 1
                    time.sleep(1)  # 等待一秒后重试
                    continue
                    
                return True
                
            except TimeoutException:
                retry_count += 1
                if retry_count >= self.max_retries:
                    self.logger.error('等待文章列表更新超时')
                    return False
                time.sleep(1)
        return False

    def parse(self, response):
        try:
            # 使用Selenium加载页面
            self.driver.get(response.url)
            
            # 等待页面加载完成
            if not self.wait_for_page_load():
                self.logger.error('页面加载失败，超过最大重试次数')
                return
            
            # 从settings获取搜索条件
            search_key1 = self.settings.get('SEARCH_KEY1', '')
            search_key2 = self.settings.get('SEARCH_KEY2', '')
            
            # 处理第一个搜索框
            if search_key1:
                search_input1 = self.wait_for_element((By.ID, 'Key1'))
                if not search_input1:
                    return
                self.logger.info('找到第一个搜索输入框')
                search_input1.clear()
                search_input1.send_keys(search_key1)
            
            # 处理第二个搜索框
            if search_key2:
                search_input2 = self.wait_for_element((By.ID, 'Key2'))
                if not search_input2:
                    return
                self.logger.info('找到第二个搜索输入框')
                search_input2.clear()
                search_input2.send_keys(search_key2)
            
            # 等待页面响应输入
            self.driver.implicitly_wait(2)
            
            # 使用更精确的XPath选择器定位查询按钮
            submit_button = self.wait_for_element(
                (By.XPATH, "//button[contains(@onclick, 'SearchData') and normalize-space(text())='查 询']")
            )
            if not submit_button:
                self.logger.error('未找到查询按钮')
                return
                
            self.logger.info('找到查询按钮，按钮文本：%s', submit_button.text)
            if not self.safe_click(submit_button):
                self.logger.error('点击查询按钮失败')
                return
            self.logger.info('成功点击查询按钮')
            
            # 等待文章列表容器加载
            if not self.wait_for_article_list_update():
                return
            self.logger.info('文章列表容器加载完成')
            
            while True:
                # 获取当前文章列表内容（用于后续验证更新）
                article_list = self.wait_for_element((By.ID, 'EtTableArticleList'))
                if not article_list:
                    return
                old_content = article_list.get_attribute('innerHTML')
                
                # 使用BeautifulSoup解析页面内容
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # 获取文章列表容器
                article_list_container = soup.select_one('.search_ext_article_list')
                if not article_list_container:
                    self.logger.error('未找到文章列表容器')
                    return
                
                # 获取文章列表
                articles = article_list_container.select('li')
                self.logger.info(f'找到 {len(articles)} 篇文章')
                
                # 提取当前页面的所有文章数据
                for article in articles:
                    try:
                        # 提取文章信息
                        title_elem = article.select_one('.search_ext_article_title a')
                        title = title_elem.get_text(strip=True) if title_elem else ''
                        
                        # 提取作者列表
                        authors = [author.get_text(strip=True) 
                                  for author in article.select('.search_ext_article_author a')]
                        
                        # 提取发布时间（不包含DOI）
                        publish_time_elem = article.select_one('.search_ext_article_position')
                        publish_time = publish_time_elem.get_text().split('DOI:')[0].strip() if publish_time_elem else ''
                        
                        # 提取关键词
                        keyword_elem = article.select_one('.search_ext_article_keyword a')
                        keywords = keyword_elem.get_text().split(',') if keyword_elem else []
                        keywords = [k.strip() for k in keywords]
                        
                        # 提取摘要
                        abstract_elem = article.select_one('.search_ext_article_abstract p')
                        abstract = abstract_elem.get_text().replace('摘要:', '').strip() if abstract_elem else ''
                        
                        # 创建文章数据项
                        yield {
                            'title': title,
                            'authors': authors,
                            'publish_time': publish_time,
                            'keywords': keywords,
                            'abstract': abstract
                        }
                    except Exception as e:
                        self.logger.error(f'解析文章时出错: {str(e)}')
                        continue
                
                try:
                    # 获取页面信息
                    page_info = self.wait_for_element((By.CSS_SELECTOR, ".t-pages span"))
                    if page_info:
                        page_text = page_info.text
                        if '共' in page_text and '页' in page_text:
                            self.total_pages = int(page_text.split('共')[1].split('页')[0].strip())
                            self.logger.info(f'总页数：{self.total_pages}')
                    
                    # 获取当前页码
                    current_page = self.wait_for_element(
                        (By.CSS_SELECTOR, "a.active[href*='SubmitArticleSearch']")
                    )
                    if not current_page:
                        self.logger.error('无法获取当前页码')
                        return
                        
                    current_page_num = int(current_page.text)
                    
                    # 检查页面是否已访问
                    if current_page_num in self.visited_pages:
                        self.logger.warning(f'页面 {current_page_num} 已访问过，跳过')
                        return
                    
                    # 标记当前页面为已访问
                    self.visited_pages.add(current_page_num)
                    self.logger.info(f'当前处理第 {current_page_num} 页')
                    
                    # 检查是否达到最大页数
                    if self.total_pages and current_page_num >= self.total_pages:
                        self.logger.info('已到达最后一页')
                        return
                    
                    # 处理分页
                    next_button = self.wait_for_element(
                        (By.CSS_SELECTOR, "a.next"),
                        timeout=30
                    )
                    if not next_button:
                        self.logger.info('未找到下一页按钮，可能已到达最后一页')
                        return
                        
                    # 检查是否为最后一页（最后一页的下一页按钮没有href属性）
                    href = next_button.get_attribute('href')
                    if not href:
                        self.logger.info('已到达最后一页，停止爬取')
                        return
                            
                    if not self.safe_click(next_button):
                        self.logger.error('点击下一页按钮失败')
                        return
                    self.logger.info('点击下一页')
                    
                    # 等待新页面加载完成并确保文章列表已更新
                    if not self.wait_for_article_list_update(old_content):
                        self.logger.error('新页面文章列表加载失败或未更新')
                        return
                        
                    # 验证页码是否正确更新
                    new_current_page = self.wait_for_element(
                        (By.CSS_SELECTOR, "a.active[href*='SubmitArticleSearch']")
                    )
                    if not new_current_page:
                        self.logger.error('无法获取新的页码')
                        return
                    
                    new_page_num = int(new_current_page.text)
                    if new_page_num <= current_page_num:
                        self.logger.error(f'页码未正确更新：当前页码 {new_page_num} 小于或等于上一页码 {current_page_num}')
                        return
                except Exception as e:
                    self.logger.error(f'处理分页时出错: {str(e)}')
                    return
                finally:
                    pass
        except Exception as e:
            self.logger.error(f'爬取过程中出错: {str(e)}')
            return
        finally:
            # 清理资源或执行其他必要的操作
            pass
