from opt import auth
import datetime
import requests
import pytz
import os

MODE = os.getenv("PYTHON_ENV", "develop")


def get_evcs_measurements(device_id, dateFrom, dateTo):
    url = "https://platmobele.cpqd.com.br/cpqd-manager/rest/containers/deviceHistory/processes/deviceHistory.deviceHistory/variables/Result"
    
    token = auth.get_access_token()
    payload = {
        "attr": "meterValuesReq",
        "device_id": device_id,
        "dateFrom": dateFrom,
        "dateTo": dateTo,
        "authorization": token
    }
    
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code >= 200 and response.status_code < 300:
        data = response.json()
        return data
    else:
        return None

if __name__ == "__main__":
# Exemplo de uso da função

    meterValuesReq = get_evcs_measurements("2262c9", "2025-02-03T00:00:00.0000Z", "2025-02-03T23:59:59.0000Z")
    a = 1