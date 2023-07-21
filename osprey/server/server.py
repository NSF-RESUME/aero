from osprey.server.app import app, db
from osprey.server.app.models import Source, SourceVersion, Proxy, Tag, Provenance, Function, SourceFile

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 
            'Source': Source, 
            'SourceVersion': SourceVersion, 
            'proxy': Proxy, 
            'tag': Tag, 
            'provenance': Provenance, 
            'function': Function,
            'SourceFile': SourceFile }
