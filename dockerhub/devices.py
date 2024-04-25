from flask_restx import Namespace, Resource, fields
from data import check
import os

from data import check
api = Namespace('devices', description='Device related operations')

# Modelo para um Device
device_model = api.model('Device', {
    'id': fields.String(required=True, description='The device identifier'),
    'name': fields.String(required=True, description='The device name'),
    'Pmax': fields.Float(required=True, description='The maximum power'),
    'Vnom': fields.Float(required=True, description='The nominal voltage'),
    'Inom': fields.Float(required=True, description='The nominal current'),
    'NDC': fields.Integer(required=True, description='Number of DC devices'),
    'NAC': fields.Integer(required=True, description='Number of AC devices'),
    'setup_id': fields.String(required=True, description='The setup identifier this device belongs to')
})

device_update_model = api.model('DeviceUpdate', {
    'name': fields.String(required=False, description='The device name'),
    'Pmax': fields.Float(required=False, description='The maximum power'),
    'Vnom': fields.Float(required=False, description='The nominal voltage'),
    'Inom': fields.Float(required=False, description='The nominal current'),
    'NDC': fields.Integer(required=False, description='Number of DC devices'),
    'NAC': fields.Integer(required=False, description='Number of AC devices')
})

@api.route('/setups/<setup_id>/devices')
@api.param('setup_id', 'The setup identifier')
class DeviceList(Resource):
    @api.marshal_list_with(device_model)
    def get(self, setup_id):
        '''List all devices for a given setup, ensuring the setup exists'''
        check.initialize_tables()
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)

        # Primeiro, verificar se o setup existe
        cursor.execute("SELECT id FROM setup WHERE id = %s", (setup_id,))
        if not cursor.fetchone():
            # Se o setup não existir, retornar erro 404
            cursor.close()
            db_connection.close()
            api.abort(404, f"Setup with id {setup_id} not found.")

        # Se o setup existir, listar todos os dispositivos associados a ele
        cursor.execute("SELECT * FROM device WHERE setup_id = %s", (setup_id,))
        devices = cursor.fetchall()

        cursor.close()
        db_connection.close()

        # Retornar a lista de dispositivos se existirem, ou uma lista vazia se não houver dispositivos
        return devices

    @api.expect(device_model)
    @api.marshal_with(device_model, code=201)
    def post(self, setup_id):
        '''Create a new device associated with a setup, ensuring both setup and device IDs are valid'''
        check.initialize_tables()
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)
        
        # Verificar se o setup existe
        cursor.execute("SELECT id FROM setup WHERE id = %s", (setup_id,))
        if not cursor.fetchone():
            cursor.close()
            db_connection.close()
            api.abort(404, f"Setup with id {setup_id} not found.")
        
        data = api.payload
        
        # Verificar se o device já existe
        cursor.execute("SELECT id FROM device WHERE id = %s", (data['id'],))
        if cursor.fetchone():
            cursor.close()
            db_connection.close()
            api.abort(409, f"Device with id {data['id']} already exists.")
        
        cursor.execute(
            "INSERT INTO device (id, name, Pmax, Vnom, Inom, NDC, NAC, setup_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (data['id'], data['name'], data['Pmax'], data['Vnom'], data['Inom'], data['NDC'], data['NAC'], setup_id)
        )
        db_connection.commit()
        cursor.close()
        db_connection.close()
        return data, 201
    
@api.route('/setups/<setup_id>/devices/<id>')
@api.param('setup_id', 'The setup identifier')
@api.param('id', 'The device identifier')
@api.response(404, 'Device not found')
class DeviceResource(Resource):
    @api.marshal_with(device_model)
    def get(self, setup_id, id):
        '''Fetch a device given its identifier and setup_id, ensuring both setup and device IDs are valid'''
        check.initialize_tables()
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)

        # Verificar se o setup existe
        cursor.execute("SELECT id FROM setup WHERE id = %s", (setup_id,))
        if not cursor.fetchone():
            cursor.close()
            db_connection.close()
            api.abort(404, f"Setup with id {setup_id} not found.")

        # Buscar o dispositivo dentro do setup fornecido
        cursor.execute("SELECT * FROM device WHERE id = %s AND setup_id = %s", (id, setup_id))
        device = cursor.fetchone()

        cursor.close()
        db_connection.close()

        # Se o dispositivo existir, retorná-lo
        if device:
            return device

        # Se o dispositivo não for encontrado, abortar com erro 404
        api.abort(404, f"Device with id {id} not found in setup with id {setup_id}.")

    @api.expect(device_update_model)
    @api.marshal_with(device_update_model)
    def put(self, setup_id, id):
        '''Update a device given its identifier and setup_id, allowing partial updates'''
        check.initialize_tables()
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)

        # Verificar se o setup existe
        cursor.execute("SELECT id FROM setup WHERE id = %s", (setup_id,))
        if not cursor.fetchone():
            cursor.close()
            db_connection.close()
            api.abort(404, f"Setup with id {setup_id} not found.")

        # Verificar se o dispositivo existe e pertence ao setup fornecido
        cursor.execute("SELECT id FROM device WHERE id = %s AND setup_id = %s", (id, setup_id))
        if not cursor.fetchone():
            cursor.close()
            db_connection.close()
            api.abort(404, f"Device with id {id} not found in setup with id {setup_id}.")

        # Construir a consulta de atualização com base nos campos fornecidos
        data = api.payload
        update_fields = []
        update_values = []

        for field, value in data.items():
            update_fields.append(f"{field} = %s")
            update_values.append(value)

        if not update_fields:
            api.abort(400, "No fields provided for update")

        update_query = f"UPDATE device SET {', '.join(update_fields)} WHERE id = %s AND setup_id = %s"
        update_values.append(id)
        update_values.append(setup_id)

        cursor.execute(update_query, tuple(update_values))
        db_connection.commit()

        # Verificar se a operação de atualização afetou alguma linha
        if cursor.rowcount == 0:
            cursor.close()
            db_connection.close()
            api.abort(404, f"Device with id {id} not found in setup with id {setup_id} or no fields updated.")

        cursor.close()
        db_connection.close()
        return {**data, "id": id, "setup_id": setup_id}, 200

    @api.response(204, 'Device successfully deleted.')
    def delete(self, setup_id, id):
        '''Delete a device given its identifier and setup_id, ensuring both setup and device IDs are valid'''
        check.initialize_tables()
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)
        
        # Verificar se o setup existe
        cursor.execute("SELECT id FROM setup WHERE id = %s", (setup_id,))
        if not cursor.fetchone():
            cursor.close()
            db_connection.close()
            api.abort(404, f"Setup with id {setup_id} not found.")
        
        # Verificar se o device existe e pertence ao setup fornecido
        cursor.execute("SELECT id FROM device WHERE id = %s AND setup_id = %s", (id, setup_id))
        if not cursor.fetchone():
            cursor.close()
            db_connection.close()
            api.abort(404, f"Device with id {id} not found in setup with id {setup_id}.")
        
        cursor.execute("DELETE FROM device WHERE id = %s AND setup_id = %s", (id, setup_id))
        db_connection.commit()
        cursor.close()
        db_connection.close()
        return '', 204
