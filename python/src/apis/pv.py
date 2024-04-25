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

    @api.expect(pv_model)
    @api.marshal_with(pv_model)
    def put(self, id):
        """Update an existing PV system"""
        data = api.payload
        initialize_tables()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE PV SET name=%s, setup_id=%s, eff=%s, Pmax=%s WHERE id=%s",
                       (data['name'], data['setup_id'], data['eff'], data['Pmax'], id))
        if cursor.rowcount == 0:
            conn.close()
            api.abort(404, "PV system not found")
        conn.commit()
        cursor.close()
        conn.close()
        return data

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
