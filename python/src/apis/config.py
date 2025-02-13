from flask_restx import Namespace, Resource, fields
from data.check import initialize_tables, get_db_connection
from data import check

# Namespace for TimeConfig
api = Namespace('timeconfig', description='Operations related to Time Configurations')

# Data model for TimeConfig
time_config_model = api.model('TimeConfig', {
    'URL': fields.String(description='URL associated with the time configuration'),
    'timestep': fields.Integer(description='Time step associated with the configuration'),
    'tmin_d': fields.String(description='Minimum daytime time in HH:MM format'),
    'tmax_d': fields.String(description='Maximum daytime time in HH:MM format'),
    'tmin_c': fields.String(description='Minimum nighttime time in HH:MM format'),
    'tmax_c': fields.String(description='Maximum nighttime time in HH:MM format')
})

# Definição do modelo de atualização parcial para Setup
time_config_update_model = api.model('TimeConfigUPDATE', {
    'URL': fields.String(required = False, description='URL associated with the time configuration'),
    'timestep': fields.Integer(required = False, description='Time step associated with the configuration'),
    'tmin_d': fields.String(required = False, description='Minimum daytime time in HH:MM format'),
    'tmax_d': fields.String(required = False, description='Maximum daytime time in HH:MM format'),
    'tmin_c': fields.String(required = False, description='Minimum nighttime time in HH:MM format'),
    'tmax_c': fields.String(required = False, description='Maximum nighttime time in HH:MM format')
})

"""

def validate_setup(setup):
    errors = []

    if 'Pmax' in setup and (setup['Pmax'] is not None):
        if setup['Pmax'] < 0:
            errors.append("Pmax must be a positive value")

    if 'Vnom' in setup and (setup['Vnom'] is not None):
        if setup['Vnom'] < 0:
            errors.append("Vnom must be a positive value")

    if 'controllable' in setup and (setup['controllable'] is not None):
        if setup['controllable'] not in ['none', 'power', 'current']:
            errors.append("controllable must be one of 'none', 'power', or 'current'")

    # Add other validation rules as needed
    # For example, checking if a field should be within a certain range or not empty
    
    return errors
"""

@api.route('/1')  # Fixed ID as part of the URL
class TimeConfigResource(Resource):
    @api.marshal_with(time_config_model)
    def get(self):
        """Fetch the single TimeConfig entry by fixed ID"""
        initialize_tables()
        conn = get_db_connection()
        if conn is None:
            api.abort(500, "Failed to connect to the database")
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM TimeConfig WHERE id = 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if not result:
            api.abort(404, "TimeConfig not found")
        return result

    @api.expect(time_config_update_model, validate=True)
    @api.marshal_with(time_config_update_model)
    def put(self, id=1):
        '''Update a config given its identifier, allowing partial updates'''
        setup = api.payload

        # Construct SQL dynamically based on provided fields
        update_fields = []
        update_values = []
        for field, value in setup.items():
            if value is not None:
                update_fields.append(f"{field} = %s")
                update_values.append(value)

        if not update_fields:
            api.abort(400, "No fields provided for update")

        update_query = f"UPDATE TimeConfig SET {', '.join(update_fields)} WHERE id = %s"
        update_values.append(id)  # Adds the id at the end of the values list for the WHERE clause

        # Connect to the database and execute the update operation
        check.initialize_tables()
        db_connection = check.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)
        try:
            cursor.execute(update_query, tuple(update_values))
            db_connection.commit()

            # Check if the update operation affected any rows (i.e., if the provided id exists)
            if cursor.rowcount == 0:
                cursor.close()
                db_connection.close()
                api.abort(404, f"Setup with id {id} not found")

            # Fetch the updated setup
            cursor.execute("SELECT * FROM TimeConfig WHERE id = %s", (id,))
            updated_setup = cursor.fetchone()

            cursor.close()
            db_connection.close()

            if not updated_setup:
                api.abort(404, "Updated TimeConfig not found")

            return updated_setup, 200

        except Exception as e:
            cursor.close()
            db_connection.close()
            api.abort(400, f"Failed to update TimeConfig record: {e}")
