from flask_restx import Namespace, Resource, fields, reqparse
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


# Modelo de dados para EVCS
update_model = api.model('UPDATE_EVCS', {
    'name': fields.String(required=False, description='The EVCS name'),
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

# Parser para o parâmetro setup_id
parser = reqparse.RequestParser()
parser.add_argument('setup_id', type=int, required=True, help='Setup ID to filter EVCS')

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
        """Add a new EVCS entry"""
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

    @api.expect(update_model, validate=True)
    @api.marshal_with(evcs_model)
    def put(self, id):
        """Update an existing EVCS entry"""
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
        
        query = f"UPDATE EVCS SET {', '.join(update_fields)} WHERE id = %s"
        try:
            cursor.execute(query, update_values)
            if cursor.rowcount == 0:
                api.abort(404, f"No EVCS found with id {id}")
            conn.commit()
        except Exception as e:
            conn.close()
            api.abort(400, f"Failed to update EVCS record: {e}")
        
        # Buscar a entrada atualizada
        cursor.execute("SELECT * FROM EVCS WHERE id = %s", (id,))
        updated_entry = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not updated_entry:
            api.abort(404, "Updated EVCS not found")
        
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
    

# # Endpoint para listar EVCS por setup_id
# @api.route('/setup')
# class EVCSBySetup(Resource):
#     @api.expect(parser)
#     @api.marshal_list_with(evcs_model)
#     def get(self):
#         """List all EVCS entries for a specific setup"""
#         args = parser.parse_args()
#         setup_id = args.get('setup_id')
#         initialize_tables()
#         conn = get_db_connection()
#         if conn is None:
#             api.abort(500, "Failed to connect to the database")
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute("SELECT * FROM EVCS WHERE setup_id = %s", (setup_id,))
#         evcs_entries = cursor.fetchall()
#         cursor.close()
#         conn.close()
#         if not evcs_entries:
#             api.abort(404, f"No EVCS found with setup_id {setup_id}")
#         return evcs_entries