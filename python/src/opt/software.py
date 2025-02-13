import os
import requests

NOTIFICATION = os.environ.get('NOTIFICATION', "TRUE")


def is_running_in_docker():
    try:
        with open('/proc/1/cgroup', 'rt') as f:
            content = f.read()
        return 'docker' in content
    except Exception:
        return False
    
def get_setups():
    if is_running_in_docker():
        base_url = 'http://nginx:80/ders/secondlayer/'
    else:
        base_url = 'http://localhost:40080/ders/secondlayer/'
    
    url = base_url + 'setups/'

    headers = {'accept': 'application/json'}
    response = requests.get(url, headers=headers)
    if response.status_code >= 200 and response.status_code < 300:
        setups = response.json()
    else:
        return None
    return setups

def get_data_by_setup_id(endpoint, setup_id):
    if is_running_in_docker():
        base_url = 'http://nginx:80/ders/secondlayer/'
    else:
        base_url = 'http://localhost:40080/ders/secondlayer/'

    url = base_url + endpoint
    headers = {'accept': 'application/json'}

    response = requests.get(url, headers=headers)
    if response.status_code >= 200 and response.status_code < 300:
        data_list = response.json()
    else:
        return None

    filtered_data = [data for data in data_list if data['setup_id'] == setup_id]

    return filtered_data

def get_evcs_by_setup_id(setup_id):
    return get_data_by_setup_id('evcs/', setup_id)

def get_bess_by_setup_id(setup_id):
    return get_data_by_setup_id('bess/', setup_id)

def get_pv_by_setup_id(setup_id):
    return get_data_by_setup_id('pv/', setup_id)

def get_v2g_by_setup_id(setup_id):
    return get_data_by_setup_id('v2g/', setup_id)

def get_timeconfig(config_id):
    # Verifica se está rodando dentro de um contêiner Docker
    if is_running_in_docker():
        base_url = 'http://nginx:80/ders/secondlayer/timeconfig/'
    else:
        base_url = 'http://localhost:40080/ders/secondlayer/timeconfig/'
    
    url = base_url + str(config_id)
    headers = {'accept': 'application/json'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return None




if __name__ == '__main__':
    setup_id = 3

    filtered_evcs = get_evcs_by_setup_id(setup_id)
    filtered_bess = get_bess_by_setup_id(setup_id)
    filtered_pv = get_pv_by_setup_id(setup_id)
    filtered_v2g = get_v2g_by_setup_id(setup_id)

    if filtered_evcs:
        print("EVCSs filtrados com sucesso:")
        print(filtered_evcs)
    else:
        print("Falha ao obter os EVCSs ou nenhum EVCS encontrado para o setup_id especificado.")

    if filtered_bess:
        print("BESSs filtrados com sucesso:")
        print(filtered_bess)
    else:
        print("Falha ao obter os BESSs ou nenhum BESS encontrado para o setup_id especificado.")

    if filtered_pv:
        print("PVs filtrados com sucesso:")
        print(filtered_pv)
    else:
        print("Falha ao obter os PVs ou nenhum PV encontrado para o setup_id especificado.")

    if filtered_v2g:
        print("V2Gs filtrados com sucesso:")
        print(filtered_v2g)
    else:
        print("Falha ao obter os V2Gs ou nenhum V2G encontrado para o setup_id especificado.")

    # Definindo a variável `a`
    a = 1
