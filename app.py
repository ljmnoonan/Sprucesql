from flask import Flask, render_template, Blueprint
import pyodbc
import os
import importlib
from pathlib import Path
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

def create_app():
    """App factory to create and configure the Flask application."""
    app = Flask(__name__)
    app.config['CONNECTION_STRING'] = conn_str

    def discover_blueprints(root_path, root_module):
        """Recursively discover and register blueprints."""
        tree = {}
        for path in root_path.iterdir():
            if not path.is_dir():
                continue

            # It's a query module if it has routes.py
            if (path / 'routes.py').exists():
                module_name = f"{root_module}.{path.name}.routes"
                module = importlib.import_module(module_name)
                for item in dir(module):
                    bp = getattr(module, item)
                    if isinstance(bp, Blueprint):
                        app.register_blueprint(bp)
                        # Store the blueprint itself for the template
                        tree[path.name] = {"blueprint": bp, "children": {}}
                        break
            # Otherwise, it's a group folder, so recurse
            else:
                subtree = discover_blueprints(path, f"{root_module}.{path.name}")
                if subtree:
                    tree[path.name] = {"blueprint": None, "children": subtree}
        return tree

    queries_root_path = Path(__file__).parent / 'queries'
    queries_tree = discover_blueprints(queries_root_path, 'queries')

    @app.route('/')
    def index():
        """Serves the main directory page, passing in discovered queries."""
        return render_template('index.html', queries_tree=queries_tree)

    return app

app = create_app()
