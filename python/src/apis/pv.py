from flask_restx import Namespace, Resource, fields
from data.check import initialize_tables, get_db_connection

# Namespace for PV systems
api = Namespace('pv', description='Operations related to Photovoltaic Systems')

# Data model for PV
pv_model = api.model('PV', {
    'id': fields.String(required=True, description='Unique identifier for the PV system'),
    'name': fields.String(required=True, description='Name of the PV system'),
    'setup_id': fields.Integer(required=True, description='ID of the associated setup'),
    'eff': fields.Float(required=True, description='Efficiency of the PV system', min=0, max=1),
    'Pmax': fields.Float(required=True, description='Maximum power capacity of the PV system', min=0)
})

update_model = api.model('UPDATE_PV', {
    'name': fields.String(required=False, description='Name of the PV system'),
    'setup_id': fields.Integer(required=False, description='ID of the associated setup'),
    'eff': fields.Float(required=False, description='Efficiency of the PV system', min=0, max=1),
    'Pmax': fields.Float(required=False, description='Maximum power capacity of the PV system', min=0)
})


@api.route('/')
class PVList(Resource):
    @api.marshal_list_with(pv_model)
    def get(self):
        """List all PV systems"""
        initialize_tables()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM PV")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results

    @api.expect(pv_model)
    @api.marshal_with(pv_model, code=201)
    def post(self):
        """Create a new PV system"""
        data = api.payload
        initialize_tables()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO PV (id, name, setup_id, eff, Pmax) VALUES (%s, %s, %s, %s, %s)",
                       (data['id'], data['name'], data['setup_id'], data['eff'], data['Pmax']))
        conn.commit()
        cursor.close()
        conn.close()
        return data, 201

@api.route('/<string:id>')
@api.param('id', 'The PV system identifier')
@api.response(404, 'PV system not found')
class PVResource(Resource):
    @api.marshal_with(pv_model)
    def get(self, id):
        """Fetch a single PV system by ID"""
        initialize_tables()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM PV WHERE id = %s", (id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return result
        api.abort(404, "PV system not found")

    @api.expect(update_model, validate=True)
    @api.marshal_with(pv_model)
    def put(self, id):
        """Update an existing PV system"""
        data = api.payload
        if not data:
            api.abort(400, "No input data provided")
            
        initialize_tables()
        conn = get_db_connection()
        if conn is None:
            api.abort(500, "Failed to connect to the database")
        cursor = conn.cursor()

        update_fields = []
        update_values = []

        for key, value in data.items():
            if value is not None:
                update_fields.append(f"{key} = %s")
                update_values.append(value)

        if not update_fields:
            api.abort(400, "No fields to update")

        update_values.append(id)

        query = f"UPDATE PV SET {', '.join(update_fields)} WHERE id = %s"
        try:
            cursor.execute(query, update_values)
            conn.commit()
            if cursor.rowcount == 0:
                cursor.close()
                conn.close()
                api.abort(404, f"No PV system found with id {id}")
        except Exception as e:
            cursor.close()
            conn.close()
            api.abort(400, f"Failed to update PV system record: {e}")

        # Buscar a entrada atualizada
        cursor.execute("SELECT * FROM PV WHERE id = %s", (id,))
        updated_entry = cursor.fetchone()

        cursor.close()
        conn.close()

        if not updated_entry:
            api.abort(404, "Updated PV system not found")

        # Mapear os resultados da consulta para o formato de dicionário esperado
        updated_data = {
            'id': updated_entry[0],
            'name': updated_entry[1],
            'setup_id': updated_entry[2],
            'eff': updated_entry[3],
            'Pmax': updated_entry[4]
        }
        
        return updated_data


    def delete(self, id):
        """Delete a PV system"""
        initialize_tables()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM PV WHERE id = %s", (id,))
        if cursor.rowcount == 0:
            conn.close()
            api.abort(404, "PV system not found")
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "PV system deleted successfully"}, 204
