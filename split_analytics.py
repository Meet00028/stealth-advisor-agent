with open('src/analytics/engine.py', 'r') as f:
    lines = f.readlines()

engine_lines = []
skip = False
for line in lines:
    if line.startswith('class RiskDetector:'):
        skip = True
    elif line.startswith('class PortfolioAnalyticsEngine:'):
        skip = False
    
    if not skip:
        engine_lines.append(line)

with open('src/analytics/engine.py', 'w') as f:
    f.writelines(engine_lines)

with open('src/analytics/risk.py', 'r') as f:
    lines = f.readlines()

risk_lines = []
keep = True
for line in lines:
    if line.startswith('@dataclass(frozen=True)'):
        keep = False
    elif line.startswith('class RiskDetector:'):
        keep = True
    elif line.startswith('class PortfolioAnalyticsEngine:'):
        keep = False
        
    if keep:
        risk_lines.append(line)

with open('src/analytics/risk.py', 'w') as f:
    f.writelines(risk_lines)
