from osprey.server.app import db
from osprey.server.app import create_app
from osprey.server.app.models import Source, SourceVersion, Proxy, Tag, Provenance, Function, SourceFile

app = create_app()

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
