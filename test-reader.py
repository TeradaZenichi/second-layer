import datetime
import requests

def get_heartbeat_data(device_id, attr, date_from, date_to):
    # URL da API
    url = "https://cs3060.cpqd.com.br/cpqd-manager/rest/containers/deviceHistory/processes/deviceHistory.deviceHistory/variables/Result"
    
    # Parâmetros da requisição
    params = {
        "device_id": device_id,
        "attr": attr,
        "dateFrom": date_from,
        "dateTo": date_to
    }
    
    # Fazendo a requisição HTTP
    response = requests.post(url, params=params)
    
    # Verificando se a requisição foi bem-sucedida
    if response.status_code == 200:
        # Convertendo a resposta JSON para um dicionário Python
        data = response.json()
    else:
        # Se a requisição falhar, retornar uma lista vazia
        data = []
    
    return data

def get_heartbeat_data_within_interval(device_id, attr, date_from, date_to, interval_minutes):
    # Obtém os dados de heartbeat usando a função de acesso aos dados
    data = get_heartbeat_data(device_id, attr, date_from, date_to)
    
    # Convertendo strings de data para objetos datetime
    date_from_dt = datetime.datetime.fromisoformat(date_from.replace("Z", "+00:00"))
    date_to_dt = datetime.datetime.fromisoformat(date_to.replace("Z", "+00:00"))
    
    # Tempo atual em UTC-3
    now_utc_minus_3 = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    
    # Intervalo de tempo em minutos
    time_threshold = now_utc_minus_3 - datetime.timedelta(minutes=interval_minutes)
    
    # Filtrando os dados com base nos parâmetros de entrada e no intervalo de tempo
    filtered_data = [
        data_entry for data_entry in data
        if date_from_dt <= datetime.datetime.fromisoformat(data_entry["ts"].replace("Z", "+00:00")) <= date_to_dt
        and datetime.datetime.fromisoformat(data_entry["ts"].replace("Z", "+00:00")) >= time_threshold
    ]
    
    return filtered_data

# Exemplo de uso da função
request = {
    "device_id": "7415ca",
    "attr": "heartbeatReq",
    "dateFrom": "2024-05-15T00:00:20.812000Z",
    "dateTo": "2024-05-15T23:59:59.812000Z"
}

# Definindo o intervalo em minutos
interval_minutes = 10

response = get_heartbeat_data_within_interval(
    device_id=request["device_id"],
    attr=request["attr"],
    date_from=request["dateFrom"],
    date_to=request["dateTo"],
    interval_minutes=interval_minutes
)

print(response)
