import json, duckdb
from pathlib import Path
serving = Path('/opt/lakehouse/data/serving')
conn = duckdb.connect()
for name in ['monthly_summary','price_metrics','commodity_comparison']:
    p = (serving / name / 'data.parquet').as_posix()
    rows = [dict(zip([d[0] for d in conn.description], r)) for r in conn.execute(f"SELECT * FROM read_parquet('{p}')").fetchall()]
    with open(f'/tmp/{name}.json', 'w') as f:
        json.dump({'status':'success','data':rows,'meta':{'count':len(rows)}}, f, default=str)
    print(f'{name}: {len(rows)} rows')
conn.close()
print('Done')
