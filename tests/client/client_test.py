# import pandas as pd

# from osprey.client import list_sources
# from osprey.client import create_source
# from osprey.client import get_file
# from osprey.client import register_function


# def register(func):
#     try:
#         response = register_function(func)
#         assert response.get("code") == 200
#         function = response.get("function_id")
#         return function
#     except Exception as e:
#         print(e)


# def failing_validator(*args, **kwargs):
#     raise KeyError


# def passing_validator(*args, **kwargs):
#     return True


# def failing_modifier(*args, **kwargs):
#     raise KeyError


# def passing_modifier(*args, **kwargs):
#     return True


# def test_list_sources():
#     # when database is not populated, assert empty
#     # assert list_sources() == []

#     # add data and assert that it is not empty
#     name = "test-1"
#     url = "https://dummyjson.com/products/1"
#     validator = register(failing_validator)
#     create_source(
#         name=name, url=url, verifier=validator, email="valeriehayot@gmail.com"
#     )
#     exp_resp = [
#         {
#             "description": None,
#             "id": 1,
#             "modifier": None,
#             "name": name,
#             "timer": 86400,
#             "url": url,
#             "verifier": validator,
#             "email": "valeriehayot@gmail.com",
#         }
#     ]
#     print(list_sources())
#     assert list_sources() == exp_resp


# def test_create_source():
#     pass


# def test_get_file():
#     assert isinstance(get_file(source_id=1, version=1), pd.DataFrame)
#     pass


# def test_list_proxies():
#     pass
