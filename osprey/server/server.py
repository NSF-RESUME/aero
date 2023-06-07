"""Flask server implementation."""
import pickle
import psycopg

from flask import Flask
from flask import request

app = Flask(__name__)
user = 'valeriehayot-sasson'


@app.route("/osprey/api/v1.0/proxies/data", methods=["GET"])
def get_proxies() -> bytes:
    """REST request to return proxy/ies to the user.
    
    Returns (bytes):
        The pickled dictionary of all proxies or a single pickled proxy if \
            database name to return is provided.
    """
    with psycopg.connect(f'dbname=osprey user={user}') as conn:
        with conn.cursor() as cur:
            
            if request.data != b"":
                cur.execute(f'''SELECT distinct on (source.name) proxy
                        FROM source LEFT JOIN metadata on source.name = metadata.name
                        WHERE source.name = \'{request.data.decode('utf-8')}\' 
                        order by source.name, version desc''')

                p =cur.fetchone()[0]
                data = pickle.dumps(p)
            else:
                cur.execute(f'''SELECT distinct on (source.name) source.name as tn, proxy
                        FROM source LEFT JOIN metadata on source.name = metadata.name
                        order by source.name, version desc''')
                data = pickle.dumps(cur.fetchall())
    return data


@app.route("/osprey/api/v1.0/proxies/metadata", methods=["GET"])
def get_metadata() -> bytes:
    """REST request to return table metadata to the user.
    
    Returns (bytes):
        The pickled list of dictionaries of all tables.
    """
    with psycopg.connect(f'dbname=osprey user={user}', row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            
            if request.data != b"":
                cur.execute(f'''SELECT source.name as tn, checksum, last_modif, version, metadata.proxy, tags.tag, provenance.parent_proxy
                        FROM source LEFT JOIN metadata on source.name = metadata.name
                        LEFT JOIN tags on tags.name = source.name
                        LEFT JOIN provenance on metadata.proxy = provenance.proxy
                        WHERE source.name = \'{request.data.decode('utf-8')}\' 
                        order by tn, version desc''')
                data = pickle.dumps(cur.fetchone())
            else:
                cur.execute(f'''SELECT source.name as tn, checksum, last_modif, version, metadata.proxy, tags.tag, provenance.parent_proxy
                        FROM source LEFT JOIN metadata on source.name = metadata.name
                        LEFT JOIN tags on tags.name = source.name
                        LEFT JOIN provenance on metadata.proxy = provenance.proxy
                        order by tn, version desc''')
                data = pickle.dumps(cur.fetchall())
    return data


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
