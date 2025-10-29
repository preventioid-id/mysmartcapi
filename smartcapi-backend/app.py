import os
from flask import Flask, jsonify
from flask_cors import CORS

# Create Flask app
app = Flask(__name__)

# Get the database URL from environment variable, default to a local sqlite DB
db_url = os.environ.get("DATABASE_URL", "sqlite:///../smartcapi.db")
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Enable CORS for all routes under /api/*, allowing requests from any origin.
# This is suitable for development.
CORS(app, resources={r"/api/*": {"origins": "*"}})

# A simple health check endpoint to verify the server is running
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

# Placeholder for other API routes.
# In a real app, these would be in separate blueprints.
@app.route("/api/interviews", methods=["GET"])
def get_interviews():
    # This is a placeholder. In a real implementation, you would query the database.
    return jsonify([{"id": 1, "title": "Sample Interview"}]), 200

if __name__ == "__main__":
    # Run the app on port 5000, accessible on the local network
    app.run(host="0.0.0.0", port=5000, debug=True)
