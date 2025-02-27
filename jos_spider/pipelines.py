import json
import pandas as pd
from itemadapter import ItemAdapter

class JosSpiderPipeline:
    def __init__(self):
        self.articles = []

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # 清理数据
        article = {
            'title': adapter.get('title', '').strip(),
            'authors': [author.strip() for author in adapter.get('authors', [])],
            'publish_time': adapter.get('publish_time', '').strip(),
            'keywords': [keyword.strip() for keyword in adapter.get('keywords', [])],
            'abstract': adapter.get('abstract', '').strip()
        }
        
        # 移除空值
        article = {k: v for k, v in article.items() if v}
        
        self.articles.append(article)
        return item

    def close_spider(self, spider):
        # 保存JSON格式
        with open('jos_articles.json', 'w', encoding='utf-8') as f:
            json.dump(self.articles, f, ensure_ascii=False, indent=2)
        
        # 保存Excel格式
        df = pd.DataFrame(self.articles)
        df.to_excel('jos_articles.xlsx', index=False, engine='openpyxl')
        
        # 保存TXT格式
        with open('jos_articles.txt', 'w', encoding='utf-8') as f:
            for article in self.articles:
                f.write('标题: ' + article.get('title', '') + '\n')
                f.write('作者: ' + ', '.join(article.get('authors', [])) + '\n')
                f.write('发布时间: ' + article.get('publish_time', '') + '\n')
                f.write('关键词: ' + ', '.join(article.get('keywords', [])) + '\n')
                f.write('摘要: ' + article.get('abstract', '') + '\n')
                f.write('\n' + '-'*50 + '\n\n')