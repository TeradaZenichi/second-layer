from flask_restx import Namespace, Resource, fields
from data.check import initialize_tables, get_db_connection

api = Namespace('bess', description='Operations related to Battery Energy Storage Systems')

bess_model = api.model('BESS', {
    'id': fields.String(required=True, description='Unique identifier for the BESS'),
    'name': fields.String(required=True, description='Name of the BESS'),
    'setup_id': fields.Integer(required=True, description='ID of the associated setup'),
    'eff': fields.Float(required=True, description='Efficiency of the BESS', min=0, max=1),
    'Pmax': fields.Float(required=True, description='Maximum power rating of the BESS', min=0),
    'Emax': fields.Float(required=True, description='Maximum energy capacity of the BESS', min=0)
})

@api.route('/')
class BESSList(Resource):
    @api.marshal_list_with(bess_model)
    def get(self):
        """List all BESS entries"""
        initialize_tables()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM BESS")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results

    @api.expect(bess_model)
    @api.marshal_with(bess_model, code=201)
    def post(self):
        """Create a new BESS entry"""
        data = api.payload
        initialize_tables()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO BESS (id, name, setup_id, eff, Pmax, Emax) VALUES (%s, %s, %s, %s, %s, %s)",
                       (data['id'], data['name'], data['setup_id'], data['eff'], data['Pmax'], data['Emax']))
        conn.commit()
        cursor.close()
        conn.close()
        return data, 201

@api.route('/<string:id>')
@api.param('id', 'The BESS identifier')
class BESSResource(Resource):
    @api.marshal_with(bess_model)
    def get(self, id):
        """Fetch a single BESS entry by ID"""
        initialize_tables()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM BESS WHERE id = %s", (id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return result
        api.abort(404, "BESS not found")

    @api.expect(bess_model)
    @api.marshal_with(bess_model)
    def put(self, id):
        """Update an existing BESS entry"""
        data = api.payload
        initialize_tables()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE BESS SET name=%s, setup_id=%s, eff=%s, Pmax=%s, Emax=%s WHERE id=%s",
                       (data['name'], data['setup_id'], data['eff'], data['Pmax'], data['Emax'], id))
        if cursor.rowcount == 0:
            conn.close()
            api.abort(404, "BESS not found")
        conn.commit()
        cursor.close()
        conn.close()
        return data

    def delete(self, id):
        """Delete a BESS entry"""
        initialize_tables()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM BESS WHERE id = %s", (id,))
        if cursor.rowcount == 0:
            conn.close()
            api.abort(404, "BESS not found")
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "BESS deleted successfully"}, 204
