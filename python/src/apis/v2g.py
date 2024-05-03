from flask_restx import Namespace, Resource, fields
from data.check import get_db_connection
import mysql.connector

# Namespace creation
api = Namespace('v2g', description='Operations related to Vehicle-to-Grid (V2G) systems')

# Data model for V2G
v2g_model = api.model('V2G', {
    'id': fields.String(required=True, description='The unique identifier for a V2G system'),
    'name': fields.String(required=True, description='The name of the V2G system'),
    'setup_id': fields.Integer(required=True, description='Associated setup ID, must be a valid setup ID'),
    'nconn': fields.Integer(required=True, description='Number of connections', enum=[1, 2, 3]),
    'control': fields.String(required=True, enum=['none', 'power', 'current'], description='Control type'),
    'conn1_type': fields.String(enum=['AC', 'DC'], description='Type of the first connector'),
    'conn1_Pmax': fields.Float(description='Maximum power of the first connector'),
    'conn1_Vnom': fields.Float(description='Nominal voltage of the first connector'),
    'conn1_Imax': fields.Float(description='Maximum current of the first connector'),
    'conn2_type': fields.String(enum=['AC', 'DC'], description='Type of the second connector', skip_none=True),
    'conn2_Pmax': fields.Float(description='Maximum power of the second connector', skip_none=True),
    'conn2_Vnom': fields.Float(description='Nominal voltage of the second connector', skip_none=True),
    'conn2_Imax': fields.Float(description='Maximum current of the second connector', skip_none=True),
    'conn3_type': fields.String(enum=['AC', 'DC'], description='Type of the third connector', skip_none=True),
    'conn3_Pmax': fields.Float(description='Maximum power of the third connector', skip_none=True),
    'conn3_Vnom': fields.Float(description='Nominal voltage of the third connector', skip_none=True),
    'conn3_Imax': fields.Float(description='Maximum current of the third connector', skip_none=True),
})

def validate_nconn(data):
    """ Validate connectors based on nconn value """
    nconn = data.get('nconn')
    errors = []
    if nconn == 1 and any(key in data for key in ['conn2_type', 'conn2_Pmax', 'conn2_Vnom', 'conn2_Imax', 'conn3_type', 'conn3_Pmax', 'conn3_Vnom', 'conn3_Imax']):
        errors.append("Only connector 1 should be specified for nconn = 1.")
    elif nconn == 2 and any(key in data for key in ['conn3_type', 'conn3_Pmax', 'conn3_Vnom', 'conn3_Imax']):
        errors.append("Only connectors 1 and 2 should be specified for nconn = 2.")
    elif nconn == 3 and not all(key in data for key in ['conn1_type', 'conn2_type', 'conn3_type']):
        errors.append("Connectors 1, 2, and 3 must all be specified for nconn = 3.")
    return errors

@api.route('/')
class V2GList(Resource):
    @api.doc('list_v2g')
    @api.marshal_list_with(v2g_model)
    def get(self):
        """List all V2G entries."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM V2G")
        v2g_entries = cursor.fetchall()
        cursor.close()
        conn.close()
        return v2g_entries

    @api.expect(v2g_model)
    @api.doc('create_v2g')
    @api.marshal_with(v2g_model, code=201)
    def post(self):
        """Create a new V2G entry."""
        data = api.payload
        errors = validate_nconn(data)
        if errors:
            api.abort(400, f"Validation error: {'; '.join(errors)}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO V2G (id, name, setup_id, nconn, control, conn1_type, conn1_Pmax, conn1_Vnom, conn1_Imax,
                                  conn2_type, conn2_Pmax, conn2_Vnom, conn2_Imax, conn3_type, conn3_Pmax, conn3_Vnom, conn3_Imax)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (data['id'], data['name'], data['setup_id'], data['nconn'], data['control'],
                 data.get('conn1_type'), data.get('conn1_Pmax'), data.get('conn1_Vnom'), data.get('conn1_Imax'),
                 data.get('conn2_type'), data.get('conn2_Pmax'), data.get('conn2_Vnom'), data.get('conn2_Imax'),
                 data.get('conn3_type'), data.get('conn3_Pmax'), data.get('conn3_Vnom'), data.get('conn3_Imax')))
            conn.commit()
        except mysql.connector.Error as err:
            cursor.close()
            conn.close()
            api.abort(400, f"Failed to insert new V2G record: {err}")
        cursor.close()
        conn.close()
        return data, 201

@api.route('/<string:id>')
@api.param('id', 'The V2G identifier')
@api.response(404, 'V2G not found')
class V2GResource(Resource):
    @api.marshal_with(v2g_model)
    def get(self, id):
        """Fetch a single V2G entry by id."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM V2G WHERE id = %s", (id,))
        v2g_entry = cursor.fetchone()
        cursor.close()
        conn.close()
        if not v2g_entry:
            api.abort(404, f"V2G with id {id} not found")
        return v2g_entry

    @api.expect(v2g_model)
    @api.marshal_with(v2g_model)
    def put(self, id):
        """Update an existing V2G entry."""
        data = api.payload
        errors = validate_nconn(data)
        if errors:
            api.abort(400, f"Validation error: {'; '.join(errors)}")
        conn = get_db_connection()
        cursor = conn.cursor()
        set_clause = ', '.join([f"{k} = %s" for k, v in data.items() if v is not None])
        values = [v for v in data.values() if v is not None] + [id]
        update_query = f"UPDATE V2G SET {set_clause} WHERE id = %s"
        try:
            cursor.execute(update_query, values)
            conn.commit()
            if cursor.rowcount == 0:
                cursor.close()
                conn.close()
                api.abort(404, f"No V2G found with id {id}")
        except mysql.connector.Error as err:
            cursor.close()
            conn.close()
            api.abort(400, f"Failed to update V2G record: {err}")
        cursor.close()
        conn.close()
        return {"message": "V2G updated successfully"}, 200

    def delete(self, id):
        """Delete a V2G entry."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM V2G WHERE id = %s", (id,))
        affected = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        if affected == 0:
            api.abort(404, f"No V2G found with id {id}")
        return {"message": "V2G deleted successfully"}, 204
