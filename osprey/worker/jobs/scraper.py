"""Database scraper implementation."""

# import json, hashlib, requests
# import psycopg2 as psycopg
# from osprey.server.lib.proxies import proxify

def get_all_source():
    from osprey.server.app import app, db
    # db.init_app(app)
    from osprey.server.app.models import Source
    sources = Source.query.all()
    result = [source.toJSON() for source in sources]
    return result

# def add_metadb_entry(name:str, url: str, checksum: str, last_modif: str, version: int, proxy: str):
#     table_name = 'metadata'
#     with psycopg.connect(f'dbname=osprey user={user}') as conn:
#         with conn.cursor() as cur:
#             cur.execute(f'INSERT INTO {table_name} VALUES (%s, %s, %s, %s, %s, %s)', (name, url, checksum, last_modif, version, proxy))
#             conn.commit()

# def get_tables() -> None:
#     """Provided list of all source tables, scrape and proxy data."""

#     with psycopg.connect(f'dbname=osprey user={user}', row_factory=psycopg.rows.namedtuple_row) as conn:
#         with conn.cursor() as cur:
#             cur.execute('''SELECT distinct on (source.name) source.name as tn, source.url as url, checksum, last_modif, version
#                         FROM source LEFT JOIN metadata on source.name = metadata.name
#                         order by tn, version desc''')
#             data = cur.fetchall()

#             for entry in data:
#                 req = requests.get(entry.url)
#                 data = req.json()
#                 new_hash = hashlib.md5(json.dumps(data).encode("utf-8")).hexdigest()
#                 last_modif = req.headers["Last-Modified"]

#                 if new_hash == entry.checksum:
#                     return

#                 validate()
#                 proxy_str = proxify(entry.tn, data)

#                 if entry.version is None:
#                     version = 1
#                 else:
#                     version += 1

#                 add_metadb_entry(name=entry.tn, url=entry.url, checksum=new_hash, last_modif=last_modif, version=version, proxy=proxy_str)


# def validate() -> None:
#     """Validate the recently modified data to ensure it meets standards"""
#     pass

# get_tables()
