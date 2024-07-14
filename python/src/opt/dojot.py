import datetime
import requests
import pytz

def check_data(url, device_id, attr, interval_minutes):
    # Calculando `dateTo` como o tempo atual em UTC
    date_to = datetime.datetime.now(pytz.utc)
    
    # Calculando `dateFrom` como `interval_minutes` antes de `dateTo`
    date_from = date_to - datetime.timedelta(minutes=interval_minutes)
    
    # Convertendo datas para strings no formato ISO 8601 com 'Z'
    date_to_str = date_to.isoformat().replace("+00:00", "Z")
    date_from_str = date_from.isoformat().replace("+00:00", "Z")
    
    # Dados do payload para a requisição
    payload = {
        "device_id": device_id,
        "attr": attr,
        "lastN": 1
        #"dateFrom": date_from_str,
        #"dateTo": date_to_str
    }
    
    # Headers da requisição
    headers = {"Content-Type": "application/json"}
    
    # Fazendo a requisição HTTP POST
    response = requests.post(url, json=payload, headers=headers)
    
    # Verificando se a requisição foi bem-sucedida
    if response.status_code >= 200 and response.status_code < 300:
        # Convertendo a resposta JSON para um dicionário Python
        data = response.json()
    else:
        # Se a requisição falhar, retornar False
        return False
    
    # Tempo atual em UTC-3
    local_tz = datetime.datetime.now().astimezone().tzinfo
    now_local = datetime.datetime.now(local_tz)
    
    # Convertendo o tempo atual para UTC
    now_utc = now_local.astimezone(pytz.utc)
    
    # Intervalo de tempo em minutos
    time_threshold = now_utc - datetime.timedelta(minutes=interval_minutes)
    
    # Filtrando os dados para garantir que estão dentro do intervalo de `interval_minutes` do tempo atual em UTC-3
    filtered_data = [
        data_entry for data_entry in data
        if datetime.datetime.fromisoformat(data_entry["ts"].replace("Z", "+00:00")) >= time_threshold
    ]
    
    # Retorna True se há dados dentro do intervalo, caso contrário False
    if len(filtered_data) > 0:
        return filtered_data[0]
    else:
        return False
    

def extract_soc(filtered_data):
    if filtered_data:
        first_entry = filtered_data[0]
        for sampled_value in first_entry.get('sampledValue', []):
            if sampled_value.get('measurand') == 'SoC':
                return sampled_value.get('value')
    return None


def set_charging_profile(device_id, connector_id, charging_rate_unit, limit):
    # URL da API
    url = 'https://cs3060.cpqd.com.br/cpqd-manager/rest/containers/setChargingProfile/processes/setChargingProfile.setChargingProfile/variables/Result'
    

    payload = {
        "deviceId": device_id,
        "connectorId": str(connector_id),
        "chargingRateUnit": charging_rate_unit,
        "startPeriod": 0,
        "limit": float(limit)
    }
    
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code >= 200 and response.status_code < 300:
        data = response.json()
        if data != {'status': 'Accepted'}:
            #try again
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code >= 200 and response.status_code < 300:
                data = response.json()
                return data
            else:
                return None
        return data
    else:
        #try again
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code >= 200 and response.status_code < 300:
            data = response.json()
            if data != {'status': 'Accepted'}:
                #try again
                response = requests.post(url, json=payload, headers=headers)
                if response.status_code >= 200 and response.status_code < 300:
                    data = response.json()
                else:
                    return None
            return data
        else:
            #try again
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code >= 200 and response.status_code < 300:
                data = response.json()
                if data != {'status': 'Accepted'}:
                    #try again
                    response = requests.post(url, json=payload, headers=headers)
                    if response.status_code >= 200 and response.status_code < 300:
                        data = response.json()
                    else:
                        return None
                return data
            else:
                return None


if __name__ == "__main__":
# Exemplo de uso da função
    request = {
        "device_id": "7415ca",
        "attr": "heartbeatReq"
    }

    # Definindo a URL da API e o intervalo em minutos
    url = "https://cs3060.cpqd.com.br/cpqd-manager/rest/containers/deviceHistory/processes/deviceHistory.deviceHistory/variables/Result"
    interval_minutes = 10

    # Verifica se há dados de heartbeat dentro do intervalo especificado
    has_data = check_data(
        url=url,
        device_id=request["device_id"],
        attr=request["attr"],
        interval_minutes=interval_minutes
    )

    print('heart beat data:')
    print(has_data)

    has_data = check_data(
        url=url,
        device_id=request["device_id"],
        attr='statusNotification',
        interval_minutes=interval_minutes
    )

    print('statusNotification data:')
    print(has_data)

    a = 1