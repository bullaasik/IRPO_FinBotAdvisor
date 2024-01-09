import requests


def get_all_currencies(api_key):
    api_url = f"https://openexchangerates.org/api/latest.json?app_id={api_key}"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        return data["rates"]
    else:
        print("Ошибка при получении данных о курсах валют")
        return {}