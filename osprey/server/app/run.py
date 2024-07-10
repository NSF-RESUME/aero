from pathlib import Path
from osprey.server.app import create_app

app = create_app()

if __name__ == "__main__":
    ssl_dir = Path(__file__).parent.parent / "ssl"
    cert = ssl_dir / "cert.pem"
    key = ssl_dir / "key.pem"
    app.run(host="0.0.0.0", port="80", ssl_context=(cert, key), debug=True)
