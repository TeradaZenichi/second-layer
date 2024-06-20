# Use a imagem oficial do Nginx como base
FROM nginx:latest

# Copie o arquivo de configuração do Nginx para o diretório de configuração do Nginx dentro do contêiner
COPY nginx-app.conf /etc/nginx/conf.d/default.conf

# Copie o arquivo de configuração principal do Nginx (se necessário)
COPY nginx.conf /etc/nginx/nginx.conf
