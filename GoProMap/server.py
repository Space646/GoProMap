from flask import Flask, send_from_directory, jsonify
import os

app = Flask(__name__)

# Folder where the JSON files are stored
json_folder = os.path.join(os.path.expanduser('~'), 'Documents', 'gps_data')

@app.route('/')
def index():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'public'), 'index.html')

@app.route('/json-files')
def json_files():
    # List all the .json files in the gps_data folder
    try:
        json_files = [f for f in os.listdir(json_folder) if f.endswith('.json')]
        return jsonify(json_files)
    except Exception as e:
        return str(e), 500

# Serve static files from the "public" folder (where your HTML and JS reside)
app.add_url_rule('/gps_data/<filename>', 'gps_data', lambda filename: send_from_directory(json_folder, filename))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
