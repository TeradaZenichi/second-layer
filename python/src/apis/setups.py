from flask_restx import Resource, fields, Namespace, reqparse, abort
from data import check

api = Namespace('setups', description='Setup related operations')

setup_model = api.model('Setup', {
    'id': fields.Integer(readOnly=True, description='The setup identifier'),
    'name': fields.String(required=True, description='The setup name'),
    'Pmax': fields.Float(required=True, description='The maximum power'),
    'Vnom': fields.Float(required=True, description='The nominal voltage'),
    'controllable': fields.String(required=True, description='Controllability type')
})

setup_update_model = api.model('SetupUpdate', {
    'name': fields.String(required=False, description='The setup name'),
    'Pmax': fields.Float(required=False, description='The maximum power'),
    'Vnom': fields.Float(required=False, description='The nominal voltage'),
    'controllable': fields.String(required=False, description='Controllability type')
})

# Model for devices response
device_model = api.model('Device', {
    'type': fields.String(description='Device type (BESS, PV, EVCS, V2G)'),
    'data': fields.Raw(description='Device data')
})

def validate_setup(data):
    errors = []
    if 'Pmax' in data and (data['Pmax'] <= 0):
        errors.append("Pmax must be a positive float.")
    if 'Vnom' in data and (data['Vnom'] <= 0):
        errors.append("Vnom must be a positive float.")
    if 'controllable' in data and data['controllable'] not in ['none', 'hourly', 'voltage']:
        errors.append("Controllable must be one of the following: 'none', 'hourly', 'voltage'.")
    return errors

@api.route('/')
class SetupList(Resource):
    @api.marshal_list_with(setup_model)
    def get(self):
        '''List all setups'''
        check.initialize_tables()
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM setup")
        setups = cursor.fetchall()
        cursor.close()
        db_connection.close()
        return setups

    @api.expect(setup_model)
    @api.marshal_with(setup_model, code=201)
    def post(self):
        '''Create a new setup'''
        setup = api.payload
        
        # Validate setup data
        errors = validate_setup(setup)
        if errors:
            abort(400, ". ".join(errors))
        
        check.initialize_tables()
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)
        cursor.execute("INSERT INTO setup (name, Pmax, Vnom, controllable) VALUES (%s, %s, %s, %s)",
                       (setup['name'], setup['Pmax'], setup['Vnom'], setup['controllable']))
        db_connection.commit()
        
        new_id = cursor.lastrowid
        setup['id'] = new_id
        
        cursor.close()
        db_connection.close()
        
        return setup, 201

@api.route('/<int:id>')
@api.param('id', 'The setup identifier')
@api.response(404, 'Setup not found')
class Setup(Resource):
    @api.marshal_with(setup_model)
    def get(self, id):
        '''Fetch a setup given its identifier'''
        check.initialize_tables()
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM setup WHERE id = %s", (id,))
        setup = cursor.fetchone()
        cursor.close()
        db_connection.close()
        if setup:
            return setup
        abort(404)

    @api.expect(setup_update_model)
    @api.marshal_with(setup_model)
    def put(self, id):
        '''Update a setup given its identifier, allowing partial updates'''
        setup = api.payload
        
        # Validate setup data
        errors = validate_setup(setup)
        if errors:
            abort(400, ". ".join(errors))

        # Construct SQL dynamically based on provided fields
        update_fields = []
        update_values = []
        for field, value in setup.items():
            update_fields.append(f"{field} = %s")
            update_values.append(value)

        if not update_fields:
            abort(400, "No fields provided for update")

        update_query = f"UPDATE setup SET {', '.join(update_fields)} WHERE id = %s"
        update_values.append(id)  # Adds the id at the end of the values list for the WHERE clause

        # Connect to the database and execute the update operation
        check.initialize_tables()
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)
        cursor.execute(update_query, tuple(update_values))
        db_connection.commit()

        # Check if the update operation affected any rows (i.e., if the provided id exists)
        if cursor.rowcount == 0:
            cursor.close()
            db_connection.close()
            abort(404, f"Setup with id {id} not found")

        cursor.close()
        db_connection.close()

        return setup, 200


    @api.response(204, 'Setup successfully deleted.')
    def delete(self, id):
        '''Delete a setup given its identifier, only if it exists'''
        check.initialize_tables()
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)
        
        # First, verify the setup exists
        cursor.execute("SELECT id FROM setup WHERE id = %s", (id,))
        setup = cursor.fetchone()
        
        if not setup:
            # If it does not exist, abort with a 404 error
            cursor.close()
            db_connection.close()
            abort(404, f"Setup with id {id} not found.")
        
        # If it exists, proceed with deletion
        cursor.execute("DELETE FROM setup WHERE id = %s", (id,))
        db_connection.commit()
        
        # Verify if the deletion operation affected any rows
        if cursor.rowcount == 0:
            # If no rows were affected, the setup was not deleted (this should be redundant due to previous check)
            cursor.close()
            db_connection.close()
            abort(404, f"Setup with id {id} not found or could not be deleted.")
        
        cursor.close()
        db_connection.close()
        return '', 204
    
@api.route('/<int:id>/devices')
@api.param('id', 'The setup identifier')
@api.response(404, 'Setup not found')
class SetupDevices(Resource):
    @api.marshal_list_with(device_model)
    def get(self, id):
        '''Fetch all devices associated with a setup given its identifier'''
        check.initialize_tables()
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)
        
        # Verify the setup exists
        cursor.execute("SELECT id FROM setup WHERE id = %s", (id,))
        setup = cursor.fetchone()
        if not setup:
            cursor.close()
            db_connection.close()
            abort(404, f"Setup with id {id} not found.")
        
        # Fetch all associated devices
        devices = []

        cursor.execute("SELECT * FROM BESS WHERE setup_id = %s", (id,))
        bess_entries = cursor.fetchall()
        for entry in bess_entries:
            devices.append({'type': 'BESS', 'data': entry})

        cursor.execute("SELECT * FROM PV WHERE setup_id = %s", (id,))
        pv_entries = cursor.fetchall()
        for entry in pv_entries:
            devices.append({'type': 'PV', 'data': entry})

        cursor.execute("SELECT * FROM EVCS WHERE setup_id = %s", (id,))
        evcs_entries = cursor.fetchall()
        for entry in evcs_entries:
            devices.append({'type': 'EVCS', 'data': entry})

        cursor.execute("SELECT * FROM V2G WHERE setup_id = %s", (id,))
        v2g_entries = cursor.fetchall()
        for entry in v2g_entries:
            devices.append({'type': 'V2G', 'data': entry})

        cursor.close()
        db_connection.close()
        
        return devices