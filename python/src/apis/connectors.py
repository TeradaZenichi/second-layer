from flask_restx import Namespace, Resource, fields
from data import check
import mysql.connector
import os


# Namespace para Connectors
api = Namespace('connectors', description='Connector related operations')

# Modelo para um Connector
connector_model = api.model('Connector', {
    'number': fields.String(required=True, description='The connector number'),
    'name': fields.String(required=True, description='The connector name'),
    'type': fields.String(required=True, description='The connector type'),
    'Pmax': fields.Float(required=True, description='The maximum power'),
    'Emax': fields.Float(required=True, description='The maximum energy'),
    'Imax': fields.Float(required=True, description='The maximum current'),
    'Vnom': fields.Float(required=True, description='The nominal voltage'),
    'eff': fields.Float(required=True, description='The efficiency'),
    'device_id': fields.String(required=True, description='The device identifier this connector belongs to')
})

connector_update_model = api.model('ConnectorUpdate', {
    'name': fields.String(required=False, description='The connector name'),
    'type': fields.String(required=False, description='The connector type'),
    'Pmax': fields.Float(required=False, description='The maximum power'),
    'Emax': fields.Float(required=False, description='The maximum energy'),
    'Imax': fields.Float(required=False, description='The maximum current'),
    'Vnom': fields.Float(required=False, description='The nominal voltage'),
    'eff': fields.Float(required=False, description='The efficiency')
})

@api.route('/devices/<device_id>/connectors')
@api.param('device_id', 'The device identifier')
class ConnectorList(Resource):
    @api.marshal_list_with(connector_model)
    def get(self, device_id):
        '''List all connectors for a given device, ensuring the device exists'''
        check.initialize_tables()
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)

        # Primeiro, verificar se o dispositivo existe
        cursor.execute("SELECT id FROM device WHERE id = %s", (device_id,))
        if not cursor.fetchone():
            # Se o dispositivo não existir, retornar erro 404
            cursor.close()
            db_connection.close()
            api.abort(404, f"Device with id {device_id} not found.")

        # Se o dispositivo existir, listar todos os conectores associados a ele
        cursor.execute("SELECT * FROM connector WHERE device_id = %s", (device_id,))
        connectors = cursor.fetchall()

        cursor.close()
        db_connection.close()

        # Retornar a lista de conectores se existirem, ou uma lista vazia se não houver conectores
        return connectors

    @api.expect(connector_model)
    @api.marshal_with(connector_model, code=201)
    def post(self, device_id):
        '''Create a new connector associated with a device, ensuring the device exists and connector number is unique per device'''
        check.initialize_tables()
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)
        
        # Verificar se o dispositivo existe
        cursor.execute("SELECT id FROM device WHERE id = %s", (device_id,))
        if not cursor.fetchone():
            cursor.close()
            db_connection.close()
            api.abort(404, f"Device with id {device_id} not found.")

        data = api.payload
        
        # Verificar se já existe um conector com o mesmo 'number' para este dispositivo
        cursor.execute("SELECT number FROM connector WHERE number = %s AND device_id = %s", (data['number'], device_id))
        if cursor.fetchone():
            cursor.close()
            db_connection.close()
            api.abort(409, f"Connector with number {data['number']} already exists for device with id {device_id}.")

        # Inserir o novo conector se as verificações acima forem bem-sucedidas
        cursor.execute("INSERT INTO connector (number, name, type, Pmax, Imax, eff, device_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (data['number'], data['name'], data['type'], data['Pmax'], data['Pmax'], data['Imax'], data['Vnom'], data['eff'], device_id))
        db_connection.commit()
        cursor.close()
        db_connection.close()
        return data, 201

@api.route('/devices/<device_id>/connectors/<number>')
@api.param('device_id', 'The device identifier')
@api.param('number', 'The connector number')
@api.response(404, 'Connector not found')
class ConnectorResource(Resource):
    @api.marshal_with(connector_model)
    def get(self, device_id, number):
        '''Fetch a connector given its number and device_id, ensuring both device and connector exist'''
        check.initialize_tables()
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)

        # Verificar se o dispositivo existe
        cursor.execute("SELECT id FROM device WHERE id = %s", (device_id,))
        if not cursor.fetchone():
            cursor.close()
            db_connection.close()
            api.abort(404, f"Device with id {device_id} not found.")

        # Verificar se o conector existe para o dispositivo fornecido
        cursor.execute("SELECT * FROM connector WHERE number = %s AND device_id = %s", (number, device_id))
        connector = cursor.fetchone()

        cursor.close()
        db_connection.close()

        # Se o conector existir, retorná-lo
        if connector:
            return connector

        # Se o conector não for encontrado, retornar erro 404
        api.abort(404, f"Connector with number {number} not found for device with id {device_id}.")

    @api.expect(connector_update_model)
    @api.marshal_with(connector_update_model)
    def put(self, device_id, number):
        '''Update a connector given its number and device_id, ensuring both device and connector exist and allowing partial updates'''
        check.initialize_tables()
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)

        # Verificar se o dispositivo existe
        cursor.execute("SELECT id FROM device WHERE id = %s", (device_id,))
        if not cursor.fetchone():
            cursor.close()
            db_connection.close()
            api.abort(404, f"Device with id {device_id} not found.")

        # Verificar se o conector existe para o dispositivo fornecido
        cursor.execute("SELECT number FROM connector WHERE number = %s AND device_id = %s", (number, device_id))
        if not cursor.fetchone():
            cursor.close()
            db_connection.close()
            api.abort(404, f"Connector with number {number} not found for device with id {device_id}.")

        data = api.payload
        update_fields = []
        update_values = []

        for field, value in data.items():
            update_fields.append(f"{field} = %s")
            update_values.append(value)

        if not update_fields:
            api.abort(400, "No fields provided for update")

        update_query = f"UPDATE connector SET {', '.join(update_fields)} WHERE number = %s AND device_id = %s"
        update_values.extend([number, device_id])

        cursor.execute(update_query, tuple(update_values))
        db_connection.commit()

        # Verificar se a operação de atualização afetou alguma linha
        if cursor.rowcount == 0:
            cursor.close()
            db_connection.close()
            api.abort(404, f"Connector with number {number} not found in device with id {device_id} or no fields updated.")

        cursor.close()
        db_connection.close()
        return {**data, "number": number, "device_id": device_id}, 200

    @api.response(204, 'Connector successfully deleted.')
    def delete(self, device_id, number):
        '''Delete a connector given its number and device_id'''
        check.initialize_tables()
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)
        cursor.execute("DELETE FROM connector WHERE number = %s AND device_id = %s", (number, device_id))
        db_connection.commit()
        cursor.close()
        db_connection.close()
        return '', 204
