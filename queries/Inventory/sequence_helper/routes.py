from flask import Blueprint, render_template, request, jsonify, current_app
import pyodbc

# Create a Blueprint for the Sequence Helper.
sequence_helper_bp = Blueprint(
    'sequence_helper',
    __name__,
    template_folder='.',
    static_folder='static',
    url_prefix='/sequence_helper'
)

# Add a 'display_name' attribute for the landing page.
sequence_helper_bp.display_name = "Sequence Helper"

@sequence_helper_bp.route('/')
def sequence_helper_page():
    """Serves the page for the Sequence Helper query."""
    return render_template('sequence_helper.html')

@sequence_helper_bp.route('/query', methods=['POST'])
def query_sequence_helper():
    """
    API endpoint for the Sequence Helper query.
    """
    try:
        data = request.get_json()
        item_param = data.get('item')
        range_param = data.get('range', 15) # Default to 15 if not provided

        if not item_param:
            return jsonify({"error": "Item parameter is missing"}), 400
        
        # Sanitize range to be a positive integer
        range_param = abs(int(range_param))

        sql_query = """
            WITH TargetItem AS (
                SELECT 
                    TRY_CAST([incom].[ReportSequence] AS INT) AS ReportSequenceInt
                FROM [InventoryCommon] [incom] (nolock)
                WHERE [incom].[Item] = ?
            )
            SELECT 
                [incom].[Item],
                [incom].[ReportSequence]
            FROM [InventoryCommon] [incom] (nolock), TargetItem
            WHERE 
                TargetItem.ReportSequenceInt IS NOT NULL
                AND TRY_CAST([incom].[ReportSequence] AS INT) BETWEEN TargetItem.ReportSequenceInt - ? AND TargetItem.ReportSequenceInt + ?
            ORDER BY TRY_CAST([incom].[ReportSequence] AS INT);
        """

        conn_str = current_app.config['CONNECTION_STRING']
        with pyodbc.connect(conn_str) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_query, item_param, range_param, range_param)
                columns = [column[0] for column in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return jsonify(results)

    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500