from flask_restx import Namespace, Resource, fields
from data.check import initialize_tables, get_db_connection

# Criação do namespace
api = Namespace('evcs', description='Operations related to EV Charging Stations')

# Modelo de dados para EVCS
evcs_model = api.model('EVCS', {
    'id': fields.String(required=True, description='The unique identifier for an EVCS'),
    'name': fields.String(required=True, description='The EVCS name'),
    'setup_id': fields.Integer(required=True, description='Associated setup ID'),
    'nconn': fields.Integer(required=True, description='Number of connections'),
    'control': fields.String(required=True, enum=['none', 'power', 'current'], description='Control type'),
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

# Endpoint para listar e criar EVCS
@api.route('/')
class EVCSList(Resource):
    @api.marshal_list_with(evcs_model)
    def get(self):
        """List all EVCS entries"""
        initialize_tables()
        conn = get_db_connection()
        if conn is None:
            api.abort(500, "Failed to connect to the database")
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM EVCS")
        evcs_entries = cursor.fetchall()
        cursor.close()
        conn.close()
        return evcs_entries

    @api.expect(evcs_model)
    @api.marshal_with(evcs_model, code=201)
    def post(self):
        """Create a new EVCS entry"""
        data = api.payload
        initialize_tables()
        conn = get_db_connection()
        if conn is None:
            api.abort(500, "Failed to connect to the database")
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO EVCS (id, name, setup_id, nconn, control, conn1_type, conn1_Pmax, conn1_Vnom, conn1_Imax,
                                  conn2_type, conn2_Pmax, conn2_Vnom, conn2_Imax, conn3_type, conn3_Pmax, conn3_Vnom, conn3_Imax)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                           (data['id'], data['name'], data['setup_id'], data['nconn'], data['control'],
                            data.get('conn1_type'), data.get('conn1_Pmax'), data.get('conn1_Vnom'), data.get('conn1_Imax'),
                            data.get('conn2_type'), data.get('conn2_Pmax'), data.get('conn2_Vnom'), data.get('conn2_Imax'),
                            data.get('conn3_type'), data.get('conn3_Pmax'), data.get('conn3_Vnom'), data.get('conn3_Imax')))
            conn.commit()
        except Exception as e:
            conn.close()
            api.abort(400, f"Failed to insert new EVCS record: {e}")
        cursor.close()
        conn.close()
        return data, 201

# Endpoint para operações específicas do EVCS identificado por ID
@api.route('/<string:id>')
@api.param('id', 'The EVCS identifier')
@api.response(404, 'EVCS not found')
class EVCSResource(Resource):
    @api.marshal_with(evcs_model)
    def get(self, id):
        """Fetch a single EVCS entry by id"""
        initialize_tables()
        conn = get_db_connection()
        if conn is None:
            api.abort(500, "Failed to connect to the database")
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM EVCS WHERE id = %s", (id,))
        evcs_entry = cursor.fetchone()
        cursor.close()
        conn.close()
        if not evcs_entry:
            api.abort(404, f"EVCS with id {id} not found")
        return evcs_entry

    @api.expect(evcs_model)
    @api.marshal_with(evcs_model)
    def put(self, id):
        """Update an existing EVCS entry"""
        data = api.payload
        initialize_tables()
        conn = get_db_connection()
        if conn is None:
            api.abort(500, "Failed to connect to the database")
        cursor = conn.cursor()
        set_clause = ', '.join([f"{k} = %s" for k, v in data.items() if v is not None])
        values = [v for v in data.values() if v is not None] + [id]
        update_query = f"UPDATE EVCS SET {set_clause} WHERE id = %s"
        try:
            cursor.execute(update_query, values)
            if cursor.rowcount == 0:
                api.abort(404, f"No EVCS found with id {id}")
            conn.commit()
        except Exception as e:
            conn.close()
            api.abort(400, f"Failed to update EVCS record: {e}")
        cursor.close()
        conn.close()
        return {"message": "EVCS updated successfully"}, 200

    def delete(self, id):
        """Delete an EVCS entry"""
        initialize_tables()
        conn = get_db_connection()
        if conn is None:
            api.abort(500, "Failed to connect to the database")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM EVCS WHERE id = %s", (id,))
        affected = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        if affected == 0:
            api.abort(404, f"No EVCS found with id {id}")
        return {"message": "EVCS deleted successfully"}, 204