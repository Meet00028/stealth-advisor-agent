import os
import re

# Fix imports in all files in src/
replacements = {
    "from data_loader import": "from utils.data_loader import",
    "from analytics import": "from analytics.engine import",  # Will fix RiskDetector later
    "from models import": "from models import",
    "from agent import FinancialAdvisorAgent": "from agents.advisor import FinancialAdvisorAgent",
    "from evaluator import SelfEvaluator": "from agents.evaluator import SelfEvaluator",
    "from intelligence import MarketIntelligence": "from intelligence.processor import MarketIntelligence", # Will adjust this
}

def replace_in_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
        
    # Replace old import lines
    content = content.replace("from agent import", "from agents.advisor import")
    content = content.replace("from evaluator import", "from agents.evaluator import")
    content = content.replace("from data_loader import", "from utils.data_loader import")
    content = content.replace("from analytics import PortfolioAnalyticsEngine, RiskDetector", "from analytics.engine import PortfolioAnalyticsEngine\nfrom analytics.risk import RiskDetector")
    content = content.replace("from analytics import DailyPnlResult", "from analytics.engine import DailyPnlResult")
    content = content.replace("from intelligence import MarketIntelligence", "from intelligence.trends import MarketIntelligence")
    
    with open(filepath, 'w') as f:
        f.write(content)

for root, dirs, files in os.walk("src"):
    for file in files:
        if file.endswith(".py"):
            replace_in_file(os.path.join(root, file))

