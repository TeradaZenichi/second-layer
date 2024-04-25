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
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            Pmax FLOAT NOT NULL CHECK (Pmax > 0),
            Vnom FLOAT NOT NULL CHECK (Vnom > 0),
            controllable ENUM('none', 'hourly', 'voltage') NOT NULL
        )
        """)
        print("Tabela 'setup' criada com sucesso!")
    else:
        print("Tabela 'setup' já existe.")
    
        # Tabela "EVCS"
    cursor.execute("SHOW TABLES LIKE 'EVCS'")
    if not cursor.fetchone():
        cursor.execute("""
        CREATE TABLE EVCS (
            id VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            setup_id INT NOT NULL,
            nconn INT NOT NULL CHECK (nconn IN (1, 2, 3)),
            control ENUM('none', 'power', 'current') NOT NULL,
            conn1_type ENUM('AC', 'DC'),
            conn1_Pmax FLOAT CHECK (conn1_Pmax > 0),
            conn1_Vnom FLOAT CHECK (conn1_Vnom > 0),
            conn1_Imax FLOAT CHECK (conn1_Imax > 0),
            conn2_type ENUM('AC', 'DC'),
            conn2_Pmax FLOAT CHECK (conn2_Pmax > 0),
            conn2_Vnom FLOAT CHECK (conn2_Vnom > 0),
            conn2_Imax FLOAT CHECK (conn2_Imax > 0),
            conn3_type ENUM('AC', 'DC'),
            conn3_Pmax FLOAT CHECK (conn3_Pmax > 0),
            conn3_Vnom FLOAT CHECK (conn3_Vnom > 0),
            conn3_Imax FLOAT CHECK (conn3_Imax > 0),
            PRIMARY KEY (id),
            FOREIGN KEY (setup_id) REFERENCES setup(id) ON DELETE CASCADE
        )
        """)
        print("Tabela 'EVCS' criada com sucesso!")

        # Criando os gatilhos para garantir a consistência dos dados com base em nconn
        cursor.execute("""
        CREATE TRIGGER before_insert_EVCS BEFORE INSERT ON EVCS
        FOR EACH ROW
        BEGIN
            IF NEW.nconn = 1 THEN
                IF NEW.conn2_type IS NOT NULL OR NEW.conn3_type IS NOT NULL THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Only conn1 should be filled when nconn is 1.';
                END IF;
            ELSEIF NEW.nconn = 2 THEN
                IF NEW.conn1_type IS NULL OR NEW.conn2_type IS NULL OR NEW.conn3_type IS NOT NULL THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Only conn1 and conn2 should be filled when nconn is 2.';
                END IF;
            ELSEIF NEW.nconn = 3 THEN
                IF NEW.conn1_type IS NULL OR NEW.conn2_type IS NULL OR NEW.conn3_type IS NULL THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'conn1, conn2, and conn3 must all be filled when nconn is 3.';
                END IF;
            END IF;
        END;
        """)
        print("Gatilhos para a tabela 'EVCS' criados com sucesso!")
    else:
        print("Tabela 'EVCS' já existe.")

    # Tabela "BESS"
    cursor.execute("SHOW TABLES LIKE 'BESS'")
    if not cursor.fetchone():
        cursor.execute("""
        CREATE TABLE BESS (
            id VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            setup_id INT NOT NULL,
            eff FLOAT NOT NULL CHECK (eff >= 0 AND eff <= 1),
            Pmax FLOAT NOT NULL CHECK (Pmax > 0),
            Emax FLOAT NOT NULL CHECK (Emax > 0),
            PRIMARY KEY (id),
            FOREIGN KEY (setup_id) REFERENCES setup(id) ON DELETE CASCADE
        )
        """)
        print("Tabela 'BESS' criada com sucesso!")
    else:
        print("Tabela 'BESS' já existe.")

    # Tabela "PV"
    cursor.execute("SHOW TABLES LIKE 'PV'")
    if not cursor.fetchone():
        cursor.execute("""
        CREATE TABLE PV (
            id VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            setup_id INT NOT NULL,
            eff FLOAT NOT NULL CHECK (eff >= 0 AND eff <= 1),
            Pmax FLOAT NOT NULL CHECK (Pmax > 0),
            PRIMARY KEY (id),
            FOREIGN KEY (setup_id) REFERENCES setup(id) ON DELETE CASCADE
        )
        """)
        print("Tabela 'PV' criada com sucesso!")
    else:
        print("Tabela 'PV' já existe.")

    # Criação da tabela "TimeConfig"
    cursor.execute("SHOW TABLES LIKE 'TimeConfig'")
    if not cursor.fetchone():
        cursor.execute("""
        CREATE TABLE TimeConfig (
            id INT PRIMARY KEY,
            URL VARCHAR(255) NOT NULL,
            timestep INT NOT NULL,
            tmin_d VARCHAR(5) NOT NULL,
            tmax_d VARCHAR(5) NOT NULL,
            tmin_c VARCHAR(5) NOT NULL,
            tmax_c VARCHAR(5) NOT NULL,
            UNIQUE (URL, timestep)
        )
        """)
        print("Tabela 'TimeConfig' criada com sucesso!")
        # Inserir valores pré-definidos
        cursor.execute("""
        INSERT INTO TimeConfig (id, URL, timestep, tmin_d, tmax_d, tmin_c, tmax_c) VALUES
        (1, 'https://cs3060.cpqd.com.br/cpqd-manager/rest/containers/deviceHistory/processes/deviceHistory.deviceHistory/variables/Result', 
        5, '18:00', '21:00', '03:00', '05:00')
        """)
        mydb.commit()
        print("Dados inseridos com sucesso na tabela 'TimeConfig'.")
    else:
        print("Tabela 'TimeConfig' já existe.")

    # close the connection
    cursor.close()
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
    