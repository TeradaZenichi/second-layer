from flask_restx import Namespace, Resource, fields
from data.check import initialize_tables, get_db_connection

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

    @api.expect(time_config_model, validate=True)
    @api.marshal_with(time_config_model)
    def put(self):
        """Update the existing TimeConfig entry by fixed ID"""
        data = api.payload
        initialize_tables()
        conn = get_db_connection()
        if conn is None:
            api.abort(500, "Failed to connect to the database")
        cursor = conn.cursor()
        # Building the update query dynamically based on provided fields
        update_fields = [f"{key} = %({key})s" for key in data if data[key] is not None]
        if not update_fields:
            api.abort(400, "No data provided for update")
        update_query = f"UPDATE TimeConfig SET {', '.join(update_fields)} WHERE id = 1"
        try:
            cursor.execute(update_query, data)
            if cursor.rowcount == 0:
                api.abort(404, "TimeConfig not found")
            conn.commit()
        except Exception as e:
            conn.close()
            api.abort(400, f"Failed to update TimeConfig: {str(e)}")
        cursor.close()
        conn.close()
        return {"message": "TimeConfig updated successfully"}, 200
