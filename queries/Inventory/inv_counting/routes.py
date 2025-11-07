from flask import Blueprint, render_template, request, jsonify, current_app, send_file
import pyodbc
import openpyxl
from io import BytesIO


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
                incom.ReportSequence, instr.Item, incom.Description,
                instr.OnHand, instr.OnOrder, instr.Committed
            FROM InventoryCommon incom (nolock) 
            INNER JOIN InventoryStore instr (nolock) on incom.Item = instr.Item
            WHERE incom.[Group] = ?
            ORDER BY TRY_CAST([incom].[ReportSequence] AS INT);
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

@inv_counting_bp.route('/download_xlsx', methods=['GET'])
def download_xlsx():
    """
    API endpoint to download the 'Item' column as an XLSX file.
    """
    group_param = request.args.get('group')
    if not group_param:
        return jsonify({"error": "Group parameter is missing"}), 400

    try:
        sql_query = "SELECT instr.Item FROM InventoryCommon incom (nolock) INNER JOIN InventoryStore instr (nolock) on incom.Item = instr.Item WHERE incom.[Group] = ?"
        
        conn_str = current_app.config['CONNECTION_STRING']
        with pyodbc.connect(conn_str) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_query, group_param)
                items = [row[0] for row in cursor.fetchall()]

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Items"
        ws.append(["Item"])  # Header
        for item in items:
            ws.append([item])

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        return send_file(output, as_attachment=True, download_name=f'items_group_{group_param}.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred during XLSX generation: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500