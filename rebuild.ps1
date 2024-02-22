docker-compose down
# docker volume rm e75_software_gestao_microrredes_mysql-data
docker-compose build
docker-compose up --remove-orphans -d
ECHO Y | docker image prune
docker-compose logs -f