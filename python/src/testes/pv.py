import requests
from opt.auth import get_access_token

def get_pv_measurements(resource_identification="4bf29d"):
    """
    Função para buscar medições do inversor (PV) usando o endpoint fornecido.

    :param resource_identification: Identificação do recurso (default: "INVERSOR_LAB")
    :return: Dados de medições do inversor ou mensagem de erro
    """
    # Obter o access_token usando a função importada
    access_token = get_access_token()
    
    # Verificar se o token foi obtido com sucesso
    if "Erro" in access_token:
        return f"Erro ao obter o access_token: {access_token}"

    # URL do endpoint
    url = "https://platmobele.cpqd.com.br/cpqd-manager/rest/containers/getResourceFvMeasurement/processes/getResourceFvMeasurement.getResourceFvMeasurement/variables/Result"
    
    # JSON payload com os dados necessários
    payload = {
        "resourceIdentification": resource_identification,  # Identificação do recurso (inversor)
        "authorization": access_token  # Access token fornecido
    }
    
    # Cabeçalhos
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        # Enviar a requisição POST
        response = requests.post(url, json=payload, headers=headers)
        
        # Verificar se a requisição foi bem-sucedida
        if response.status_code == 200:
            return response.json()  # Retorna a resposta em JSON
        else:
            # Retornar mensagem de erro em caso de falha
            return f"Erro: {response.status_code}, {response.text}"
    
    except Exception as e:
        return f"Erro ao fazer a requisição: {e}"

# Exemplo de uso
if __name__ == "__main__":
    response = get_pv_measurements()
    print(response)
    a = 1