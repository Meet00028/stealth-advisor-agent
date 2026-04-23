import json
from pathlib import Path
from typing import List, Dict, Any
from src.models import NewsArticle, IndexData, SectorPerformance, StockData, Portfolio

class DataLoader:
    """I implemented this ingestion engine to read our JSON data directly from the data directory."""

    def __init__(self, data_dir: str = None):
        """I initialize the loader with the directory containing our real JSON files."""
        if data_dir is None:
            # Resolve the path to the root 'data' directory (two levels up from this file)
            current_dir = Path(__file__).resolve().parent
            data_dir = str(current_dir.parent.parent / "data")
        self.data_dir = Path(data_dir)

    def _load_json(self, filename: str) -> Any:
        """I built this helper to safely load JSON files and handle missing files gracefully."""
        file_path = self.data_dir / filename
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: I could not find {filename} in {self.data_dir}. Returning empty dictionary/list.")
            return {}
        except json.JSONDecodeError:
            print(f"Error: I failed to parse {filename} due to invalid JSON. Returning empty dictionary/list.")
            return {}

    def get_news(self) -> List[NewsArticle]:
        """I parse the news articles from the 'news' list in news_data.json."""
        data = self._load_json("news_data.json")
        news_list = data.get("news", []) if isinstance(data, dict) else []
        return [NewsArticle(**item) for item in news_list]

    def get_market_indices(self) -> Dict[str, IndexData]:
        """I load and parse market indices from the 'indices' dictionary in market_data.json."""
        data = self._load_json("market_data.json")
        indices_dict = data.get("indices", {}) if isinstance(data, dict) else {}
        
        parsed_indices = {}
        for symbol, item_data in indices_dict.items():
            item_data["symbol"] = symbol
            parsed_indices[symbol] = IndexData(**item_data)
        return parsed_indices

    def get_sector_performance(self) -> Dict[str, SectorPerformance]:
        """I load and parse sector performance from the 'sector_performance' dictionary in market_data.json."""
        data = self._load_json("market_data.json")
        sectors_dict = data.get("sector_performance", {}) if isinstance(data, dict) else {}
        
        parsed_sectors = {}
        for sector_name, item_data in sectors_dict.items():
            item_data["sector_name"] = sector_name
            parsed_sectors[sector_name] = SectorPerformance(**item_data)
        return parsed_sectors

    def get_stocks(self) -> Dict[str, StockData]:
        """I load and parse individual stock data from the 'stocks' dictionary in market_data.json."""
        data = self._load_json("market_data.json")
        stocks_dict = data.get("stocks", {}) if isinstance(data, dict) else {}
        
        parsed_stocks = {}
        for ticker, item_data in stocks_dict.items():
            item_data["ticker"] = ticker
            parsed_stocks[ticker] = StockData(**item_data)
        return parsed_stocks

    def get_portfolio(self, portfolio_id: str) -> Portfolio:
        """I load and validate a specific portfolio from portfolios.json by its portfolio_id key."""
        data = self._load_json("portfolios.json")
        portfolios = data.get("portfolios", {}) if isinstance(data, dict) else {}
        if portfolio_id not in portfolios:
            raise ValueError(f"I could not find portfolio_id={portfolio_id} in portfolios.json")
        portfolio_data = dict(portfolios[portfolio_id])
        portfolio_data["portfolio_id"] = portfolio_id
        return Portfolio(**portfolio_data)

    def get_mutual_funds(self) -> Dict[str, Dict[str, Any]]:
        """I load mutual funds as a raw dictionary from mutual_funds.json for downstream analytics enrichment."""
        data = self._load_json("mutual_funds.json")
        mutual_funds = data.get("mutual_funds", {}) if isinstance(data, dict) else {}
        if isinstance(mutual_funds, dict):
            return mutual_funds
        return {}

    def get_sector_mapping(self) -> Dict[str, Any]:
        return self._load_json("sector_mapping.json")
