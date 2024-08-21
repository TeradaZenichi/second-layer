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


update_model = api.model('UPDATE_BESS', {
    'name': fields.String(required=False, description='Name of the BESS'),
    'setup_id': fields.Integer(required=False, description='ID of the associated setup'),
    'eff': fields.Float(required=False, description='Efficiency of the BESS', min=0, max=1),
    'Pmax': fields.Float(required=False, description='Maximum power rating of the BESS', min=0),
    'Emax': fields.Float(required=False, description='Maximum energy capacity of the BESS', min=0)
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



    @api.expect(update_model, validate=True)
    @api.marshal_with(bess_model)
    def put(self, id):
        """Update an existing BESS entry"""
        data = api.payload
        if not data:
            api.abort(400, "No input data provided")
            
        initialize_tables()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        update_fields = []
        update_values = []
        
        if 'name' in data:
            update_fields.append("name=%s")
            update_values.append(data['name'])
        if 'setup_id' in data:
            update_fields.append("setup_id=%s")
            update_values.append(data['setup_id'])
        if 'eff' in data:
            update_fields.append("eff=%s")
            update_values.append(data['eff'])
        if 'Pmax' in data:
            update_fields.append("Pmax=%s")
            update_values.append(data['Pmax'])
        if 'Emax' in data:
            update_fields.append("Emax=%s")
            update_values.append(data['Emax'])
        
        if not update_fields:
            api.abort(400, "No fields to update")
        
        update_values.append(id)
        
        query = f"UPDATE BESS SET {', '.join(update_fields)} WHERE id=%s"
        cursor.execute(query, update_values)
        
        if cursor.rowcount == 0:
            conn.close()
            api.abort(404, "BESS not found")
        
        conn.commit()
        
        # Buscar a entrada atualizada
        cursor.execute("SELECT id, name, setup_id, eff, Pmax, Emax FROM BESS WHERE id=%s", (id,))
        updated_entry = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not updated_entry:
            api.abort(404, "Updated BESS not found")
        
        return {
            'id': updated_entry[0],
            'name': updated_entry[1],
            'setup_id': updated_entry[2],
            'eff': updated_entry[3],
            'Pmax': updated_entry[4],
            'Emax': updated_entry[5]
        }

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
