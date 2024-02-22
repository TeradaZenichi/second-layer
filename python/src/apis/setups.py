from flask_restx import Resource, fields, Namespace
from data import check

api = Namespace('setups', description='Setup related operations')

setup_model = api.model('Setup', {
    'id': fields.String(required=True, description='The setup identifier'),
    'name': fields.String(required=True, description='The setup name'),
    'Pmax': fields.Float(required=True, description='The maximum power')
})

setup_update_model = api.model('SetupUpdate', {
    'name': fields.String(required=False, description='The setup name'),
    'Pmax': fields.Float(required=False, description='The maximum power')
})

@api.route('/')
class SetupList(Resource):
    @api.marshal_list_with(setup_model)
    def get(self):
        '''List all setups'''
        check.initialize_tables()
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM setup")
        setups = cursor.fetchall()
        cursor.close()
        db_connection.close()
        return setups

    @api.expect(setup_model)
    @api.marshal_with(setup_model, code=201)
    def post(self):
        '''Create a new setup'''
        check.initialize_tables()
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)
        
        setup = api.payload
        # Verificar se já existe um setup com o mesmo id
        cursor.execute("SELECT id FROM setup WHERE id = %s", (setup['id'],))
        existing_setup = cursor.fetchone()
        
        if existing_setup:
            cursor.close()
            db_connection.close()
            api.abort(409, f"A setup with id {setup['id']} already exists.")
        
        # Se não existir, inserir o novo setup
        cursor.execute("INSERT INTO setup (id, name, Pmax) VALUES (%s, %s, %s)",
                    (setup['id'], setup['name'], setup['Pmax']))
        db_connection.commit()
        
        cursor.close()
        db_connection.close()
        
        return setup, 201

@api.route('/<id>')
@api.param('id', 'The setup identifier')
@api.response(404, 'Setup not found')
class Setup(Resource):
    @api.marshal_with(setup_model)
    def get(self, id):
        '''Fetch a setup given its identifier'''
        check.initialize_tables()
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM setup WHERE id = %s", (id,))
        setup = cursor.fetchone()
        cursor.close()
        db_connection.close()
        if setup:
            return setup
        api.abort(404)

    @api.expect(setup_update_model)
    @api.marshal_with(setup_update_model)
    def put(self, id):
        '''Update a setup given its identifier, allowing partial updates'''
        setup = api.payload  # Dados fornecidos para a atualização

        # Construir a string SQL dinamicamente com base nos campos fornecidos
        update_fields = []
        update_values = []
        for field, value in setup.items():
            update_fields.append(f"{field} = %s")
            update_values.append(value)

        if not update_fields:
            api.abort(400, "No fields provided for update")

        update_query = f"UPDATE setup SET {', '.join(update_fields)} WHERE id = %s"
        update_values.append(id)  # Adiciona o id ao final da lista de valores para a cláusula WHERE

        # Conectar ao banco de dados e executar a operação de atualização
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)
        cursor.execute(update_query, tuple(update_values))
        db_connection.commit()

        # Verificar se a operação de atualização afetou alguma linha (ou seja, se o id fornecido existe)
        if cursor.rowcount == 0:
            cursor.close()
            db_connection.close()
            api.abort(404, f"Setup with id {id} not found")

        cursor.close()
        db_connection.close()

        return {**setup, "id": id}, 200


    @api.response(204, 'Setup successfully deleted.')
    def delete(self, id):
        '''Delete a setup given its identifier, only if it exists'''
        check.initialize_tables()
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)
        
        # Primeiro, verificar se o setup existe
        cursor.execute("SELECT id FROM setup WHERE id = %s", (id,))
        setup = cursor.fetchone()
        
        if not setup:
            # Se não existir, abortar com um erro 404
            cursor.close()
            db_connection.close()
            api.abort(404, f"Setup with id {id} not found.")
        
        # Se existir, proceder com a exclusão
        cursor.execute("DELETE FROM setup WHERE id = %s", (id,))
        db_connection.commit()
        
        # Verificar se a operação de exclusão afetou alguma linha
        if cursor.rowcount == 0:
            # Se nenhuma linha foi afetada, o setup não foi excluído (isso deve ser redundante devido à verificação anterior)
            cursor.close()
            db_connection.close()
            api.abort(404, f"Setup with id {id} not found or could not be deleted.")
        
        cursor.close()
        db_connection.close()
        return '', 204
