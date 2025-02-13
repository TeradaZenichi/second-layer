import requests

def get_access_token():
    # URL do endpoint
    url = "https://platmobele.cpqd.com.br/auth/realms/portal/protocol/openid-connect/token"
    
    # Dados necessários para a requisição
    payload = {
        "client_id": "gders-api",
        "grant_type": "password",
        "scope": "openid",
        "username": "adm",
        "password": "#Pl4tm0b@cpqd"
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

# Exemplo de uso
token = get_access_token()
print(token)

a=1