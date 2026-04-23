from src.utils.data_loader import DataLoader

class TrendAnalyzer:
    """I analyze index movements and sector trends dynamically."""

    def __init__(self, loader: DataLoader):
        self.loader = loader

    def get_macro_sentiment(self) -> str:
        """
        I calculate the macro sentiment based on the NIFTY50 index change_percent.
        Returns strings like 'STRONG BEARISH', 'BEARISH', 'NEUTRAL', 'BULLISH', 'STRONG BULLISH'.
        """
        indices = self.loader.get_market_indices()
        
        nifty_data = indices.get("NIFTY50")
        
        if not nifty_data:
            return "UNKNOWN"
            
        change = nifty_data.change_percent
        
        if change <= -1.0:
            return "STRONG BEARISH"
        elif change < 0.0:
            return "BEARISH"
        elif change == 0.0:
            return "NEUTRAL"
        elif change >= 1.0:
            return "STRONG BULLISH"
        else:
            return "BULLISH"
