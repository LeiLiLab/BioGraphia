from flask import Flask, jsonify, send_from_directory, request
import os
import json
from flask_cors import CORS

app = Flask(__name__, static_folder='../frontend/dist')
# Enable CORS for all routes and origins with proper configuration
CORS(app, origins=["*"], supports_credentials=True, allow_headers=["Content-Type", "Authorization"])

@app.route('/api/graph', methods=['GET'])
def get_graph():
    try:
        # Use absolute path to ensure file is found
        current_dir = os.path.dirname(os.path.abspath(__file__))
        graph_file_path = os.path.join(os.path.dirname(current_dir), 'graph.json')

        print("*****************request**********************")
        print(graph_file_path)
        print("*****************request**********************")
        
        with open(graph_file_path, 'r') as file:
            graph_data = json.load(file)
        
        # Add CORS headers directly to the response
        response = jsonify(graph_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response
    except Exception as e:
        print(f"Error loading graph data: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Serve the frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    # Bind to 0.0.0.0 to allow external access
    app.run(host='0.0.0.0', debug=True) 