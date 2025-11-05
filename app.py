from flask import Flask, render_template_string, request, jsonify
import pyodbc
import os

# --- Configuration ---
# Fetch configuration from environment variables
DB_SERVER = os.environ.get('DB_SERVER')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')
DB_ENCRYPT = os.environ.get('DB_ENCRYPT') # Get the encryption setting

# Check if all required environment variables are set
if not all([DB_SERVER, DB_NAME, DB_USER, DB_PASS]):
    raise KeyError("Missing one or more database environment variables (DB_SERVER, DB_NAME, DB_USER, DB_PASS)")

# Important: Use the driver name that will be installed in the Docker container.
DB_DRIVER = '{ODBC Driver 18 for SQL Server}'

# Connection string
# Build the connection string
conn_str = f'DRIVER={DB_DRIVER};SERVER={DB_SERVER};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASS};TrustServerCertificate=yes'

# Append the Encrypt setting if the environment variable is provided
if DB_ENCRYPT:
    conn_str += f';Encrypt={DB_ENCRYPT}'

# --- Flask App Initialization ---
app = Flask(__name__)

# --- HTML Template ---
# For simplicity, the HTML is embedded in the Python script.
# In a larger app, you would save this in a separate 'templates/index.html' file.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SQL Query Runner</title>
    <style>
        body { font-family: sans-serif; margin: 2em; background-color: #f4f4f9; }
        .container { max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        input { width: 100%; padding: 8px; margin: 10px 0; box-sizing: border-box; }
        button { padding: 10px 15px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        #results { margin-top: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        #error { color: red; }
        #loading { color: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Query Inventory by Group</h1>
        <p>Enter a group number to search for.</p>
        <form id="queryForm">
            <label for="groupNumber">Group Number:</label>
            <input type="text" id="groupNumber" name="groupNumber" placeholder="e.g., 38">
            <button type="submit">Run Query</button>
        </form>
        <div id="error"></div>
        <div id="loading"></div>
        <div id="results"></div>
    </div>

    <script>
        document.getElementById('queryForm').addEventListener('submit', async function(event) {
            event.preventDefault(); // Prevent default form submission
            
            const groupNumber = document.getElementById('groupNumber').value;
            const resultsDiv = document.getElementById('results');
            const errorDiv = document.getElementById('error');
            const loadingDiv = document.getElementById('loading');

            resultsDiv.innerHTML = '';
            errorDiv.innerHTML = '';
            loadingDiv.innerHTML = 'Loading...';

            try {
                const response = await fetch('/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ group: groupNumber })
                });

                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.error || 'An unknown error occurred.');
                }

                const data = await response.json();
                
                if (data.length === 0) {
                    resultsDiv.innerHTML = '<p>No results found.</p>';
                    return;
                }

                // Create HTML table from the JSON data
                let table = '<table><thead><tr>';
                const headers = Object.keys(data[0]);
                headers.forEach(header => table += `<th>${header}</th>`);
                table += '</tr></thead><tbody>';

                data.forEach(row => {
                    table += '<tr>';
                    headers.forEach(header => {
                        // Handle null values gracefully
                        const cellData = row[header] === null ? '' : row[header];
                        table += `<td>${cellData}</td>`
                    });
                    table += '</tr>';
                });

                table += '</tbody></table>';
                resultsDiv.innerHTML = table;

            } catch (error) {
                errorDiv.innerHTML = `Error: ${error.message}`;
            } finally {
                loadingDiv.innerHTML = '';
            }
        });
    </script>
</body>
</html>
"""

# --- API Routes ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/query', methods=['POST'])
def run_query():
    """Receives a request, queries the database, and returns data as JSON."""
    try:
        # Get the parameter from the incoming JSON request
        data = request.get_json()
        group_param = data.get('group')

        if not group_param:
            return jsonify({"error": "Group parameter is missing"}), 400

        # --- YOUR PRESET SQL QUERY GOES HERE ---
        # Use '?' as a placeholder for parameters to prevent SQL injection.
        sql_query = """
            SELECT
                incom.[Group],
                instr.Item,
                incom.Description,
                instr.OnHand,
                instr.OnOrder,
                instr.Committed
            FROM 
                InventoryCommon incom (nolock) 
            INNER JOIN 
                InventoryStore instr (nolock) on incom.Item = instr.Item
            WHERE incom.[Group] = ?
        """

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Execute the query with the parameter
        cursor.execute(sql_query, group_param)
        
        # Fetch data and convert it to a list of dictionaries
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify(results)

    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"Database Error: {sqlstate}")
        # Provide a more specific error message for connection issues
        if '08001' in sqlstate:
             return jsonify({"error": "Database connection failed. Check server address and credentials."}), 500
        return jsonify({"error": "Database query failed."}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

# --- Main Execution ---
if __name__ == '__main__':
    # To make it accessible on your network, use host='0.0.0.0'
    # The 'debug=True' is great for development but should be False in production.
    # Docker Compose will manage the debug state.
    app.run(host='0.0.0.0', port=5000)
