import json, psycopg
conn = psycopg.connect('host=postgres port=5432 dbname=oil_warehouse user=arash password=warehouse_dev_2026')
cur = conn.cursor()
cur.execute('SELECT * FROM warehouse.v_latest_prices')
cols = [d.name for d in cur.description]
rows = [dict(zip(cols, r)) for r in cur.fetchall()]
with open('/tmp/latest.json', 'w') as f:
    json.dump({'status':'success','data':rows,'meta':{'count':len(rows)}}, f, default=str)
print(f'latest: {len(rows)} rows')
cur.execute('SELECT * FROM warehouse.v_price_history ORDER BY trade_date DESC LIMIT 500')
cols = [d.name for d in cur.description]
rows = [dict(zip(cols, r)) for r in cur.fetchall()]
with open('/tmp/history.json', 'w') as f:
    json.dump({'status':'success','data':rows,'meta':{'count':len(rows)}}, f, default=str)
print(f'history: {len(rows)} rows')
conn.close()
print('Done')
