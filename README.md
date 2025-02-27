# JOS Spider

这是一个用于爬取中国计算机学会JOS期刊（jos.org.cn）文章信息的爬虫项目。

## 功能特点

- 基于Scrapy框架开发
- 支持自动爬取文章列表和详情页
- 实现反爬虫机制（请求头随机化、IP代理等）
- 使用Selenium处理动态加载内容
- 数据以JSON格式输出

## 环境要求

- Python 3.8+
- Chrome浏览器（用于Selenium）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 安装依赖包
2. 配置环境变量（可选）
3. 运行爬虫：

```bash
cd JosSpider
scrapy crawl jos
```

# Local Run Command
```bash
pipenv install
pipenv shell
pipenv install requests
scrapy crawl jos
```

## 输出数据

爬虫将输出包含以下字段的JSON格式数据：

- 标题（title）
- 作者（authors）
- 发布时间（publish_time）
- DOI（doi）
- 关键词（keywords）

## 注意事项

- 请遵守网站的robots.txt规则
- 建议设置适当的爬取间隔，避免对目标网站造成压力
- 仅用于学术研究目的，请勿用于商业用途