from flask import Blueprint, render_template, request, jsonify, current_app
import pyodbc

# Create a Blueprint. This configuration tells Flask that this module has its own
# templates and static files located in the same directory.
inv_counting_bp = Blueprint(
    'inv_counting',
    __name__,
    template_folder='.',
    static_folder='static',
    url_prefix='/inv_counting'
)

# Add a 'display_name' attribute to the blueprint for the landing page.
inv_counting_bp.display_name = "Inventory Counting by Group"

@inv_counting_bp.route('/')
def inv_counting_page():
    """Serves the page for the Inventory Counting query."""
    return render_template('inv_counting.html')

@inv_counting_bp.route('/query', methods=['POST'])
def query_inv_counting():
    """
    API endpoint for the Inventory Counting query.
    """
    try:
        data = request.get_json()
        group_param = data.get('group')

        if not group_param:
            return jsonify({"error": "Group parameter is missing"}), 400

        sql_query = """
            SELECT
                incom.[Group], instr.Item, incom.Description,
                instr.OnHand, instr.OnOrder, instr.Committed
            FROM InventoryCommon incom (nolock) 
            INNER JOIN InventoryStore instr (nolock) on incom.Item = instr.Item
            WHERE incom.[Group] = ?
        """

        # Access the connection string from the main app's config
        conn_str = current_app.config['CONNECTION_STRING']
        with pyodbc.connect(conn_str) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_query, group_param)
                columns = [column[0] for column in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return jsonify(results)

    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        current_app.logger.error(f"Database Error: {sqlstate}")
        if '08001' in sqlstate:
             return jsonify({"error": "Database connection failed."}), 500
        return jsonify({"error": "Database query failed."}), 500
    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500