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

update_model = api.model('UPDATE_V2G', {
    'name': fields.String(required=False, description='The V2G name'),
    'setup_id': fields.Integer(required=False, description='Associated setup ID'),
    'nconn': fields.Integer(required=False, description='Number of connections'),
    'control': fields.String(required=False, enum=['none', 'power', 'current'], description='Control type'),
    'conn1_type': fields.String(enum=['AC', 'DC'], description='Type of the first connector'),
    'conn1_Pmax': fields.Float(description='Maximum power for the first connector'),
    'conn1_Vnom': fields.Float(description='Nominal voltage for the first connector'),
    'conn1_Imax': fields.Float(description='Maximum current for the first connector'),
    'conn2_type': fields.String(enum=['AC', 'DC'], description='Type of the second connector'),
    'conn2_Pmax': fields.Float(description='Maximum power for the second connector'),
    'conn2_Vnom': fields.Float(description='Nominal voltage for the second connector'),
    'conn2_Imax': fields.Float(description='Maximum current for the second connector'),
    'conn3_type': fields.String(enum=['AC', 'DC'], description='Type of the third connector'),
    'conn3_Pmax': fields.Float(description='Maximum power for the third connector'),
    'conn3_Vnom': fields.Float(description='Nominal voltage for the third connector'),
    'conn3_Imax': fields.Float(description='Maximum current for the third connector'),
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

    @api.expect(update_model, validate=True)
    @api.marshal_with(v2g_model)
    def put(self, id):
        """Update an existing V2G entry."""
        data = api.payload
        errors = validate_nconn(data)
        if errors:
            api.abort(400, f"Validation error: {'; '.join(errors)}")

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

        query = f"UPDATE V2G SET {', '.join(update_fields)} WHERE id = %s"
        try:
            cursor.execute(query, update_values)
            conn.commit()
            if cursor.rowcount == 0:
                cursor.close()
                conn.close()
                api.abort(404, f"No V2G found with id {id}")
        except Exception as e:
            cursor.close()
            conn.close()
            api.abort(400, f"Failed to update V2G record: {e}")

        # Buscar a entrada atualizada
        cursor.execute("SELECT * FROM V2G WHERE id = %s", (id,))
        updated_entry = cursor.fetchone()

        cursor.close()
        conn.close()

        if not updated_entry:
            api.abort(404, "Updated V2G not found")

        # Mapear os resultados da consulta para o formato de dicionário esperado
        updated_data = {
            'id': updated_entry[0],
            'name': updated_entry[1],
            'setup_id': updated_entry[2],
            'nconn': updated_entry[3],
            'control': updated_entry[4],
            'conn1_type': updated_entry[5],
            'conn1_Pmax': updated_entry[6],
            'conn1_Vnom': updated_entry[7],
            'conn1_Imax': updated_entry[8],
            'conn2_type': updated_entry[9],
            'conn2_Pmax': updated_entry[10],
            'conn2_Vnom': updated_entry[11],
            'conn2_Imax': updated_entry[12],
            'conn3_type': updated_entry[13],
            'conn3_Pmax': updated_entry[14],
            'conn3_Vnom': updated_entry[15],
            'conn3_Imax': updated_entry[16]
        }
        
        return updated_data

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
