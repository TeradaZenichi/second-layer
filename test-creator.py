import requests

# Configuração da URL base do serviço
base_url = "http://localhost:48080/ders/secondlayer"

def create_setup():
    """Cria um setup e retorna o ID gerado."""
    setup_data = {
        "name": "sistema_teste",
        "Pmax": 70,
        "Vnom": 220,
        "controllable": "none"
    }
    response = requests.post(f"{base_url}/setups/", json=setup_data)
    if response.status_code == 201:
        return response.json()['id']  # Obtemos o ID do setup a partir da resposta
    else:
        raise Exception(f"Failed to create setup: {response.status_code}, {response.text}")

def create_evcs(setup_id, evcs_data):
    """Cria um dispositivo EVCS associado ao setup_id."""
    evcs_data['setup_id'] = setup_id  # Inclui o setup_id no payload
    response = requests.post(f"{base_url}/evcs", json=evcs_data)
    if response.status_code != 201:
        raise Exception(f"Failed to create EVCS: {response.status_code}, {response.text}")

if __name__ == '__main__':
    # Criação do setup e obtenção do ID
    setup_id = create_setup()
    print(f"Setup created with ID: {setup_id}")

    # Dados para os dispositivos EVCS
    evcs1_data = {
        "id": "7415ca",
        "name": "ABBTACW745020G0166",
        "nconn": 1,
        "control": "current",
        "conn1_type": "DC",
        "conn1_Pmax": 50,
        "conn1_Vnom": 220,
        "conn1_Imax": 125
    }

    evcs2_data = {
        "id": "146b36",
        "name": "EPPARREIRA",
        "nconn": 1,
        "control": "current",
        "conn1_type": "DC",
        "conn1_Pmax": 50,
        "conn1_Vnom": 220,
        "conn1_Imax": 125
    }

    # Criação dos dispositivos EVCS associados ao setup
    create_evcs(setup_id, evcs1_data)
    print(f"EVCS '{evcs1_data['name']}' created successfully with setup ID {setup_id}.")

    create_evcs(setup_id, evcs2_data)
    print(f"EVCS '{evcs2_data['name']}' created successfully with setup ID {setup_id}.")
