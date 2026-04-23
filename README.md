# Autonomous Financial Advisor Agent

An advanced, autonomous reasoning agent that ingests market data, analyzes user portfolios, and generates causal explanations linking macro news to sector trends to individual stock performances. Built with FastAPI, LangChain, and Langfuse for observability.

## Quick Start

1. **Clone the repository** (if not already done) and enter the directory.

2. **Set up the Python environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Ensure you have a `.env` file in the root directory (where `src/` and `data/` live). It should look like this:
   ```env
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-your-openai-api-key
   
   # Langfuse Tracing Keys
   LANGFUSE_SECRET_KEY=sk-lf-...
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_HOST=https://us.cloud.langfuse.com
   ```

4. **Run the Server**:
   ```bash
   # Ensure you are in the root directory
   python -m uvicorn src.main:app --reload
   ```

5. **Test the API**:
   Open a new terminal and hit the endpoint with a mock portfolio ID (e.g., `PORTFOLIO_001`, `PORTFOLIO_002`, `PORTFOLIO_003`):
   ```bash
   curl -s http://127.0.0.1:8000/api/v1/analyze_portfolio/PORTFOLIO_002 | python3 -m json.tool
   ```

## Architecture & Modularity

The repository is structured to mirror a professional production service, adhering strictly to clean code design principles.

```text
stealth-advisor-agent/
├── data/                  # Mock JSON files (Portfolios, Market, News)
├── src/
│   ├── agents/            # Phase 3: Reasoning & Causal Linking
│   │   ├── advisor.py     # Main Agent logic (Macro -> Sector -> Stock)
│   │   └── evaluator.py   # Phase 4: Self-Evaluation LLM Judge
│   ├── analytics/         # Phase 2: Math & Risk logic
│   │   ├── engine.py      # P&L and Allocation calculations
│   │   └── risk.py        # Concentration risk detection
│   ├── intelligence/      # Phase 1: Market & News processing
│   │   ├── processor.py   # News filtering & entity matching
│   │   └── trends.py      # Index & Macro sentiment analysis
│   ├── utils/             # Utilities
│   │   └── data_loader.py # Loads and parses raw JSONs to Pydantic models
│   ├── models.py          # Pydantic schemas for structured data
│   └── main.py            # API Entry Point (FastAPI orchestration)
├── .env                   # API Keys
└── requirements.txt       # Dependencies
```

## The Reasoning Layer

This agent goes far beyond data dumping. Using advanced prompt engineering, it is strictly forced to execute **causal linking**:
`Macro News -> Sector Trends -> Individual Stock Performance -> User Portfolio Impact`. 

The news is pre-filtered dynamically in Python (via `NewsProcessor`) to ensure the LLM only reasons over `HIGH`/`MEDIUM` impact news that explicitly match the user's holdings or sector exposure, drastically reducing token usage and hallucinations.

## Self-Evaluation & Observability

- **Observability**: Fully integrated with **Langfuse**. The `@observe()` decorator tracks functions across the pipeline, and the `langfuse_context.flush()` ensures traces are safely pushed before the thread dies.
- **Evaluation Layer**: After the briefing is generated, a completely decoupled `SelfEvaluator` agent (running on a stricter model with `temperature=0.0`) grades the output on a scale of 1-5. It checks for deep causal reasoning and explicitly flags any factual inconsistencies.

---

# Financial Advisor Agent - Mock Dataset

This directory contains comprehensive mock data for the Autonomous Financial Advisor Agent challenge.

## Dataset Overview

| File | Description | Key Data Points |
|------|-------------|-----------------|
| `market_data.json` | Real-time market data snapshot | 40+ stocks, 5 indices, 10 sectors |
| `news_data.json` | Financial news feed | 25 articles with sentiment, scope, and entity tags |
| `portfolios.json` | User portfolio samples | 3 portfolios (Diversified, Sector-heavy, Conservative) |
| `mutual_funds.json` | Mutual fund details | 12 schemes with NAV, holdings, and returns |
| `historical_data.json` | 7-day historical trends | Index/stock history, FII/DII data, market breadth |
| `sector_mapping.json` | Sector-stock relationships | Macro correlations and sector characteristics |

## Data Scenarios Included

### Market Conditions (April 21, 2026)

The dataset simulates a **risk-off market day** with the following characteristics:

- **NIFTY 50**: -1.00% (Bearish)
- **Bank Nifty**: -2.33% (Strong selling due to RBI stance)
- **NIFTY IT**: +1.22% (Outperforming due to US tech earnings)
- **FII**: Net sellers of ₹4,500 crore
- **Market Breadth**: Weak (12 advances vs 38 declines in NIFTY 50)

### Sector Performance

| Sector | Day Change | Sentiment | Key Driver |
|--------|------------|-----------|------------|
| Banking | -2.45% | Bearish | RBI hawkish stance |
| IT | +1.35% | Bullish | US tech earnings, weak rupee |
| Pharma | +0.78% | Bullish | USFDA approvals |
| Metals | -1.50% | Bearish | China demand concerns |
| Realty | -2.10% | Bearish | Interest rate sensitivity |
| FMCG | +0.25% | Neutral | Defensive buying |

### News Categories

1. **Market-Wide** (5 articles)
   - RBI monetary policy
   - FII outflows
   - Global risk-off sentiment
   - Oil price movements

2. **Sector-Specific** (8 articles)
   - US tech earnings (IT positive)
   - China steel demand (Metals negative)
   - Housing sales vs rate concerns (Realty mixed)
   - Government capex push (Infra positive)

3. **Stock-Specific** (12 articles)
   - HDFC Bank results (mixed)
   - Sun Pharma USFDA approval (positive)
   - Infosys mega deal win (positive)
   - Tata Motors EV leadership (positive)

### Edge Cases for Agent Testing

The dataset includes several **conflict scenarios** to test the agent's reasoning:

1. **Positive news + Negative price action**
   - Bajaj Finance: Strong asset quality but stock falling due to sector sentiment
   - HUL: Slightly up despite weak volume growth (defensive buying)

2. **Mixed signals**
   - Reliance: Strong retail but weak Jio subscriber growth
   - Housing sales: Record high but rate concerns dominate
   - ICICI Bank: Improved asset quality but margin compression

3. **Sector vs Stock divergence**
   - Tata Motors: +0.79% vs Auto sector -1.85% (EV leadership)

## Portfolio Profiles

### Portfolio 1: Diversified (Rahul Sharma)
- **Type**: Well-balanced across sectors
- **Day P&L**: -0.44% (₹-12,785)
- **Concentration Risk**: None
- **Max Single Stock Weight**: 7.17% (TCS)
- **Asset Mix**: 38% Stocks, 62% Mutual Funds

### Portfolio 2: Sector-Concentrated (Priya Patel)
- **Type**: Banking & Financial Services heavy
- **Day P&L**: -2.73% (₹-57,390)
- **Concentration Risk**: CRITICAL (91.58% in Banking + FS)
- **Max Single Stock Weight**: 22.62% (HDFC Bank)
- **Asset Mix**: 91% Stocks, 9% Mutual Funds

### Portfolio 3: Conservative (Arun Krishnamurthy)
- **Type**: Mutual fund heavy with defensive stocks
- **Day P&L**: -0.04% (₹-1,758)
- **Concentration Risk**: None
- **Max Single Stock Weight**: 5.19% (ITC)
- **Asset Mix**: 21% Stocks, 79% Mutual Funds (34% Debt Funds)

## Usage in Agent

### Loading Data

```python
from utils.data_loader import DataLoader

# Initialize loader
loader = DataLoader()

# Load all data
portfolios = loader._load_json("portfolios.json")
news = loader.get_news()

# Get specific portfolio
portfolio = loader.get_portfolio("PORTFOLIO_002")
```

### Expected Agent Outputs

For **Portfolio 2** (Banking concentrated), the agent should identify:

1. **Primary Impact**: RBI's hawkish stance hitting all banking holdings
2. **Concentration Risk Alert**: 91.58% exposure to interest-rate sensitive sectors
3. **Causal Chain**: 
   ```
   RBI Hawkish Stance → Banking Sector -2.45% → 
   HDFC Bank -3.51% (largest holding) → Portfolio -2.73%
   ```
4. **Conflicting Signals**: 
   - ICICI Bank asset quality improved but NIM compressed
   - Bajaj Finance strong guidance but sector headwinds

## Data Schema Reference

### Stock Object
```json
{
  "symbol": "HDFCBANK",
  "name": "HDFC Bank Ltd",
  "sector": "BANKING",
  "current_price": 1542.30,
  "change_percent": -3.51,
  "volume": 15234500,
  "beta": 1.15
}
```

### News Object
```json
{
  "id": "NEWS001",
  "headline": "...",
  "sentiment": "NEGATIVE",
  "sentiment_score": -0.72,
  "scope": "MARKET_WIDE|SECTOR_SPECIFIC|STOCK_SPECIFIC",
  "impact_level": "HIGH|MEDIUM|LOW",
  "entities": {
    "sectors": ["BANKING"],
    "stocks": ["HDFCBANK"],
    "indices": ["BANKNIFTY"]
  },
  "causal_factors": ["..."]
}
```

### Portfolio Holding Object
```json
{
  "symbol": "HDFCBANK",
  "quantity": 100,
  "avg_buy_price": 1520.00,
  "current_price": 1542.30,
  "weight_in_portfolio": 5.36,
  "day_change_percent": -3.51
}
```

## Extending the Dataset

To add more scenarios:

1. **Add New Stocks**: Update `market_data.json` → `stocks` section
2. **Add News**: Update `news_data.json` → `news` array
3. **Add Portfolios**: Update `portfolios.json` → `portfolios` section
4. **Add Sector**: Update `sector_mapping.json` → `sectors` section
