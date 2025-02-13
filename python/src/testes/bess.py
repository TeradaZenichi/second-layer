import requests
from opt.auth import get_access_token

def get_bess_measurements(identification="a22162"):
    """
    Função para buscar medições do BESS usando o endpoint fornecido.

    :param identification: Identificação do BESS (default: "BESS_LAB")
    :return: Dados de medições do BESS ou mensagem de erro
    """
    # Obter o access_token usando a função importada
    access_token = get_access_token()
    
    # Verificar se o token foi obtido com sucesso
    if "Erro" in access_token:
        return f"Erro ao obter o access_token: {access_token}"

    # URL do endpoint
    url = "https://platmobele.cpqd.com.br/cpqd-manager/rest/containers/getMeasurementsBess/processes/getMeasurementsBess.getMeasurementsBess/variables/Result"
    
    # JSON payload com os dados necessários
    payload = {
        "identification": identification,  # Identificação do BESS
        "authorization": access_token      # Access token fornecido
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
    response = get_bess_measurements()
    print(response)
    a = 1