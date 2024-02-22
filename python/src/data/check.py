from mysql.connector import Error
import mysql.connector
import os

def initialize_tables():
    # Conectar-se ao banco de dados
    password = os.getenv('MYSQL_ROOT_PASSWORD')
    database = os.getenv('MYSQL_DATABASE')
    user = os.getenv('MYSQL_USER', 'root')  # Define 'root' como padrão se MYSQL_USER não estiver definido
    host = os.getenv('MYSQL_HOST', 'localhost')  # Define 'localhost' como padrão se MYSQL_HOST não estiver definido
    port = os.getenv('MYSQL_PORT', '3306')  # Define '3306' como padrão se MYSQL_PORT não estiver definido
    mydb = mysql.connector.connect(
        user=user, 
        password=password,
        host=host, 
        port=port, 
        database=database
    )

    # Verificar se as tabelas já existem e criar se necessário
    cursor = mydb.cursor()
    
    # Tabela "setup"
    cursor.execute("SHOW TABLES LIKE 'setup'")
    if not cursor.fetchone():
        cursor.execute("""
        CREATE TABLE setup (
            id VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            Pmax FLOAT NOT NULL,
            PRIMARY KEY (id)
        )
        """)
        print("Tabela 'setup' criada com sucesso!")
    else:
        print("Tabela 'setup' já existe.")

    # Tabela "device"
    cursor.execute("SHOW TABLES LIKE 'device'")
    if not cursor.fetchone():
        cursor.execute("""
        CREATE TABLE device (
            id VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            Pmax FLOAT NOT NULL,
            Vnom FLOAT NOT NULL,
            Inom FLOAT NOT NULL,
            NDC INT NOT NULL,
            NAC INT NOT NULL,
            setup_id VARCHAR(255) NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY (setup_id) REFERENCES setup(id) ON DELETE CASCADE
        )
        """)
        print("Tabela 'device' criada com sucesso!")
    else:
        print("Tabela 'device' já existe.")

    # Tabela "connector"
    cursor.execute("SHOW TABLES LIKE 'connector'")
    if not cursor.fetchone():
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS connector (
            number INT NOT NULL,
            name VARCHAR(255) NOT NULL,
            type VARCHAR(255) NOT NULL,
            Pmax FLOAT NOT NULL,
            Emax FLOAT NOT NULL,
            Imax FLOAT NOT NULL,
            Vnom FLOAT NOT NULL,
            eff FLOAT NOT NULL,
            device_id VARCHAR(255) NOT NULL,
            PRIMARY KEY (number, device_id),  -- Fazendo 'number' e 'device_id' uma chave primária composta
            FOREIGN KEY (device_id) REFERENCES device(id) ON DELETE CASCADE,
            UNIQUE (number, device_id)  -- Garantindo que a combinação de 'number' e 'device_id' seja única
        );
        """)
        print("Tabela 'connector' criada com sucesso!")
    else:
        print("Tabela 'connector' já existe.")

    # Fechar a conexão com o banco de dados
    mydb.close()


def get_db_connection():
    # Lê as variáveis de ambiente necessárias para a conexão
    password = os.getenv('MYSQL_ROOT_PASSWORD')
    database = os.getenv('MYSQL_DATABASE')
    user = os.getenv('MYSQL_USER', 'root')  # Define 'root' como padrão se MYSQL_USER não estiver definido
    host = os.getenv('MYSQL_HOST', 'localhost')  # Define 'localhost' como padrão se MYSQL_HOST não estiver definido
    port = os.getenv('MYSQL_PORT', '3306')  # Define '3306' como padrão se MYSQL_PORT não estiver definido

    # Estabelece a ão com o banco de dados
    try:
        mydb = mysql.connector.connect(
            user=user, 
            password=password,
            host=host, 
            port=port, 
            database=database
        )
        return mydb
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao banco de dados: {err}")
        return None
    
