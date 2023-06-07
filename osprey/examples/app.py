from osprey.client import get_proxy
from osprey.client import get_metadata

tn = "COVID-19 Daily Cases, Deaths, and Hospitalizations"

def max_covid_cases() -> int:
    df = get_proxy(tn)
    return df["cases_total"].max()


print(f"Max COVID-19 cases: {max_covid_cases()}")

print(get_metadata(''))
