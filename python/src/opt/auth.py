import requests
import os
NOTIFICATION = os.environ.get('NOTIFICATION', "TRUE")


def get_access_token():
    user = os.getenv("PLATMOBLE_USER", "adm")
    password = os.getenv("PLATMOBLE_PASSWORD", "#Pl4tm0b@cpqd")

    # URL do endpoint
    url = "https://platmobele.cpqd.com.br/auth/realms/portal/protocol/openid-connect/token"
    
    # Dados necessários para a requisição
    payload = {
        "client_id": "gders-api",
        "grant_type": "password",
        "scope": "openid",
        "username": user,
        "password": password
    }
    
    # Cabeçalhos (se necessário)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        # Enviar a requisição POST
        response = requests.post(url, data=payload, headers=headers)
        
        # Verificar se a requisição foi bem-sucedida
        if response.status_code == 200:
            # Parsear a resposta para JSON
            data = response.json()
            # Retornar o access_token
            return data.get("access_token", "Access token não encontrado.")
        else:
            # Retornar mensagem de erro em caso de falha
            return f"Erro: {response.status_code}, {response.text}"
    
    except Exception as e:
        return f"Erro ao fazer a requisição: {e}"


if __name__ == "__main__":
    # Exemplo de uso
    token = get_access_token()
    print(token)

    a=1