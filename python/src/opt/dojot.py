from opt import auth
import datetime
import requests
import pytz
import os

NOTIFICATION = os.environ.get('NOTIFICATION', "TRUE")
MODE = os.getenv("PYTHON_ENV", "develop")


def check_data(url, device_id, attr, interval_minutes):
    url = "https://platmobele.cpqd.com.br/cpqd-manager/rest/containers/deviceHistory/processes/deviceHistory.deviceHistory/variables/Result"
    
    protocol = None

    # Calculando `dateTo` como o tempo atual em UTC
    date_to = datetime.datetime.now(pytz.utc)
    
    # Calculando `dateFrom` como `interval_minutes` antes de `dateTo`
    date_from = date_to - datetime.timedelta(minutes=interval_minutes)
    
    # Convertendo datas para strings no formato ISO 8601 com 'Z'
    date_to_str = date_to.isoformat().replace("+00:00", "Z")
    date_from_str = date_from.isoformat().replace("+00:00", "Z")
    
    # Dados do payload para a requisição
    if MODE == "test":
        payload = {
            "device_id": device_id,
            "attr": attr,
            "lastN": 1
            #"dateFrom": date_from_str,
            #"dateTo": date_to_str
        }
    else:
        token = auth.get_access_token()
        payload = {
            "device_id": device_id,
            "attr": attr,
            "lastN": 1,
            "authorization": token
        }

    # Headers da requisição
    headers = {"Content-Type": "application/json"}
    
    # Fazendo a requisição HTTP POST
    response = requests.post(url, json=payload, headers=headers)
    
    # Verificando se a requisição foi bem-sucedida
    if response.status_code >= 200 and response.status_code < 300:
        # Convertendo a resposta JSON para um dicionário Python
        data = response.json()
        try:
            if data[0]['value']['version'] == '201':
                protocol = "OCPP 2.0.1"
            elif data[0]['value']['version'] == '16':
                protocol = "OCPP 1.6"
        except:
            pass

    else:
        # Se a requisição falhar, retornar False
        return protocol, False
    
    #get heartbeatReq mandatory
    if MODE == "test":
        url = "https://platmobele.cpqd.com.br/cpqd-manager/rest/containers/deviceHistory/processes/deviceHistory.deviceHistory/variables/Result"
        payload = {
            "device_id": device_id,
            "attr": "heartbeatReq",
            "lastN": 1
        }
        heartbeat = requests.post(url, json=payload, headers=headers)
        if heartbeat.status_code >= 200 and heartbeat.status_code < 300:
            heartbeat_data = heartbeat.json()
        else:
            heartbeat_data = False
    else:
        url = "https://platmobele.cpqd.com.br/cpqd-manager/rest/containers/deviceHistory/processes/deviceHistory.deviceHistory/variables/Result"
        token = auth.get_access_token()
        payload = {
            "device_id": device_id,
            "attr": "heartbeatReq",
            "lastN": 1,
            "authorization": token
        }
        heartbeat = requests.post(url, json=payload, headers=headers)
        if heartbeat.status_code >= 200 and heartbeat.status_code < 300:
            heartbeat_data = heartbeat.json()
        else:
            heartbeat_data = False

    
    # Tempo atual em UTC-3
    local_tz = datetime.datetime.now().astimezone().tzinfo
    now_local = datetime.datetime.now(local_tz)
    
    # Convertendo o tempo atual para UTC
    now_utc = now_local.astimezone(pytz.utc)
    
    # Intervalo de tempo em minutos
    time_threshold = now_utc - datetime.timedelta(minutes=interval_minutes)
    
    # Filtrando os dados para garantir que estão dentro do intervalo de `interval_minutes` do tempo atual em UTC-3
    #filtered_data = [
    #    data_entry for data_entry in data
    #    if datetime.datetime.fromisoformat(data_entry["ts"].replace("Z", "+00:00")) >= time_threshold
    #]
    # heartbeat_data = [{'attr': 'heartbeatReq', 'value': {'chargePoint': 'ABBTACW745020G0166', 'deviceId': '2262c9', 'command': 'Heartbeat', 'version': '16', 'correlationId': '5102972'}, 'device_id': '2262c9', 'ts': '2025-01-28T18:49:27.799000Z', 'metadata': {}}]
    # data = [{'attr': 'statusNotificationReq', 'value': {'connectorId': 1, 'errorCode': 'NoError', 'info': 'null', 'status': 'Available', 'vendorErrorCode': '0x0000', 'chargePoint': 'ABBTACW745020G0166', 'deviceId': '2262c9', 'command': 'StatusNotification', 'version': '16', 'correlationId': '4145022'}, 'device_id': '2262c9', 'ts': '2025-01-28T04:44:17.146000Z', 'metadata': {}}]

    # verifique se data e heartbeat são do mesmo dia mês e ano
    if data and heartbeat_data:
        data_day = datetime.datetime.fromisoformat(data[0]["ts"].replace("Z", "+00:00")).day
        data_month = datetime.datetime.fromisoformat(data[0]["ts"].replace("Z", "+00:00")).month
        data_year = datetime.datetime.fromisoformat(data[0]["ts"].replace("Z", "+00:00")).year
        heartbeat_day = datetime.datetime.fromisoformat(heartbeat_data[0]["ts"].replace("Z", "+00:00")).day
        heartbeat_month = datetime.datetime.fromisoformat(heartbeat_data[0]["ts"].replace("Z", "+00:00")).month
        heartbeat_year = datetime.datetime.fromisoformat(heartbeat_data[0]["ts"].replace("Z", "+00:00")).year
        if data_day == heartbeat_day and data_month == heartbeat_month and data_year == heartbeat_year:
            #verifique se o heartbeat está dentro do intervalo
            if datetime.datetime.fromisoformat(heartbeat_data[0]["ts"].replace("Z", "+00:00")) >= time_threshold:
                filtered_data = data
        else:
            filtered_data = []

    # Retorna True se há dados dentro do intervalo, caso contrário False
    try:
        if len(filtered_data) > 0:
            return protocol, filtered_data[0]
        else:
            return protocol, False
    except:
        return protocol, False
    

def extract_soc(filtered_data):
    if filtered_data:
        first_entry = filtered_data[0]
        for sampled_value in first_entry.get('sampledValue', []):
            if sampled_value.get('measurand') == 'SoC':
                return sampled_value.get('value')
    return None


def set_charging_profile(device_id, connector_id, charging_rate_unit, limit, protocol):
    # URL da API
    url = 'https://cs3060.cpqd.com.br/cpqd-manager/rest/containers/setChargingProfile/processes/setChargingProfile.setChargingProfile/variables/Result'
    
    platmoble = "https://platmobele.cpqd.com.br/cpqd-manager/rest/containers/setChargingProfile/processes/setChargingProfile.setChargingProfile/variables/Result"
    
    if MODE == "test":
        url = url
        payload = {
            "deviceId": device_id,
            "connectorId": str(connector_id),
            "chargingRateUnit": charging_rate_unit,
            "startPeriod": 0,
            "limit": float(limit),
            "ocppProtocolVersion": "OCPP 1.6"
        }
    else:
        url = platmoble
        token = auth.get_access_token()
        if protocol:
            payload = {
                "deviceId": device_id,
                "connectorId": str(connector_id),
                "chargingRateUnit": charging_rate_unit,
                "startPeriod": 0,
                "limit": float(limit),
                "ocppProtocolVersion": protocol,
                "authorization": token
            }
        else:
            payload = {
                "deviceId": device_id,
                "connectorId": str(connector_id),
                "chargingRateUnit": charging_rate_unit,
                "startPeriod": 0,
                "limit": float(limit),
                "authorization": token,
                "ocppProtocolVersion": "OCPP 1.6"
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
    token = auth.get_access_token()
    # Definindo a URL da API e o intervalo em minutos
    url = "https://platmobele.cpqd.com.br/cpqd-manager/rest/containers/deviceHistory/processes/deviceHistory.deviceHistory/variables/Result"
    interval_minutes = 10

    # Verifica se há dados de heartbeat dentro do intervalo especificado
    has_data = check_data(
        url=url,
        device_id=request["device_id"],
        attr=request["attr"],
        
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