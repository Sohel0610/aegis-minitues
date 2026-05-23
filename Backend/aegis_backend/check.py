import psycopg2
conn = psycopg2.connect('postgresql://postgres:postgres@192.168.0.56:5436/aegis_insider')
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='compliance_cache_violations'")
print([r[0] for r in cur.fetchall()])
