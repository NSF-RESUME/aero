from flask import jsonify
from osprey.server.app import app, db

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'status': 404, 'message':'Cannot find the page you are looking for'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'status':404, 'message' : 'Unexpected error has occured'}), 500
