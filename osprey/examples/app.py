from osprey.client import get_proxy


def max_covid_cases() -> int:
    df = get_proxy("COVID-19 Daily Cases, Deaths, and Hospitalizations")
    return df["cases_total"].max()


print(f"Max COVID-19 cases: {max_covid_cases()}")
