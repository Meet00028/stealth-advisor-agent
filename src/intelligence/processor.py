from typing import List
from src.utils.data_loader import DataLoader
from src.models import NewsArticle
from langfuse.decorators import observe

class NewsProcessor:
    """I built this intelligence layer to process and filter news based on the real schema."""

    def __init__(self, loader: DataLoader):
        self.loader = loader

    @observe()
    def filter_relevant_news(self, target_sectors: List[str], target_stocks: List[str]) -> List[NewsArticle]:
        """
        I filter the loaded news to return only relevant articles.
        I include articles where impact_level is HIGH or MEDIUM, AND
        the scope is MARKET_WIDE or the entities match target sectors/stocks.
        """
        all_news = self.loader.get_news()
        relevant_news = []
        
        target_sectors_lower = {s.lower() for s in target_sectors}
        target_stocks_lower = {s.lower() for s in target_stocks}
        
        for article in all_news:
            if article.impact_level.upper() not in ["HIGH", "MEDIUM"]:
                continue
                
            if article.scope.upper() == "MARKET_WIDE":
                relevant_news.append(article)
                continue
                
            article_sectors = {s.lower() for s in article.entities.sectors}
            article_stocks = {s.lower() for s in article.entities.stocks}
            
            if (target_sectors_lower & article_sectors) or (target_stocks_lower & article_stocks):
                relevant_news.append(article)
                
        return relevant_news
