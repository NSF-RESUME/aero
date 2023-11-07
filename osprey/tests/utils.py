from osprey.client import register_function

DUMMY_URL='https://dummyjson.com/products/1'
SERVER_URL = 'http://127.0.0.1:5001/osprey/api/v1.0/'

def gc_register(func):
    try:
        response = register_function(func)
        assert response.get('code') == 200
        function = response.get('function_id')
        return function
    except Exception as e:
        print(e)
