from opt.auth import get_access_token
import requests
import os

NOTIFICATION = os.environ.get('NOTIFICATION', "TRUE")


def send_command_to_manager(access_token, p_manual):
    # URL do endpoint atualizado
    url = "https://platmobele.cpqd.com.br/cpqd-manager/rest/containers/bessComandSet/processes/bessComandSet.bessComandSet/variables/Result"
    
    # JSON payload com os dados necessários
    payload = {
        "bessCommand": "inv_p_q",
        "deviceId": "97778d",
        "der_identification": "identification",
        "der_type": "BESS",
        "p_manual": p_manual,  # Valor fornecido como parâmetro
        "q_manual": 0,         # Sempre 0, conforme especificado
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
    # Obter o access_token (use a função anterior para isso)
    access_token = get_access_token()  # Certifique-se de que a função get_access_token esteja implementada
    
    if "Erro" not in access_token:  # Verificar se o token foi obtido corretamente
        # Definir um valor para p_manual
        p_manual_value = 50  # Exemplo de valor
        response = send_command_to_manager(access_token, p_manual_value)
        print(response)
    else:
        print("Erro ao obter o access_token:", access_token)
