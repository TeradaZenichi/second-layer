import requests

url = 'http://localhost:40080/ders/secondlayer/evcs/'
headers = {
    'accept': 'application/json',
    'Content-Type': 'application/json'
}
data = {
    "id": "62fbd6",
    "name": "EWOLF-26",
    "setup_id": 5,
    "nconn": 1,
    "control": "current",
    "conn1_type": "DC",
    "conn1_Pmax": 30,
    "conn1_Vnom": 380,
    "conn1_Imax": 100
}

response = requests.post(url, headers=headers, json=data)

print(response.status_code)
print(response.json())

data = {
    "id": "7415ca",
    "name": "ABBTACW745020G0166",
    "setup_id": 5,
    "nconn": 1,
    "control": "current",
    "conn1_type": "DC",
    "conn1_Pmax": 7,
    "conn1_Vnom": 220,
    "conn1_Imax": 32
}

response = requests.post(url, headers=headers, json=data)

print(response.status_code)
print(response.json())
