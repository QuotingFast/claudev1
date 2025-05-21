import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Configuration (Read from Environment Variables) ---
# IMPORTANT: Do NOT hardcode these values directly in the code.
# Set these as environment variables in your Render dashboard.
PLAYHT_USER_ID = os.environ.get("PLAYHT_USER_ID")
PLAYHT_SECRET_KEY = os.environ.get("PLAYHT_SECRET_KEY")
PLAYHT_AGENT_ID = os.environ.get("PLAYHT_AGENT_ID") # e.g., "Transfer-person-HONMb6R4LPUkQwAryiO1q"

# Play.ht API endpoint for making calls
PLAYHT_API_URL = "https://api.play.ht/v2/calls"

@app.route('/playht-webhook', methods=['POST'])
def handle_playht_webhook():
    """
    Receives lead data from Zapier, formats it, and sends it to Play.ht's API.
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    zapier_data = request.get_json()

    # Extract name and phone number from Zapier's payload
    # Adjust these keys if Zapier sends them differently (e.g., 'lead_name', 'lead_phone')
    customer_name = zapier_data.get('name')
    phone_number = zapier_data.get('phoneNumber')

    if not customer_name or not phone_number:
        return jsonify({"error": "Missing 'name' or 'phoneNumber' in request"}), 400

    # Construct the payload for Play.ht API
    playht_payload = {
        "agentId": PLAYHT_AGENT_ID,
        "phoneNumber": phone_number,
        "userId": PLAYHT_USER_ID,
        "context": {
            "customerName": customer_name
        }
    }

    # Set up headers for Play.ht API
    playht_headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-User-ID": PLAYHT_USER_ID,
        "X-Secret-Key": PLAYHT_SECRET_KEY
    }

    try:
        # Make the POST request to Play.ht API
        response = requests.post(PLAYHT_API_URL, json=playht_payload, headers=playht_headers)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

        playht_response_data = response.json()
        print(f"Successfully sent call request to Play.ht: {playht_response_data}")
        return jsonify({"status": "success", "playht_response": playht_response_data}), 200

    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error calling Play.ht: {errh}")
        return jsonify({"status": "error", "message": f"Play.ht API HTTP Error: {errh}", "playht_error_details": errh.response.text}), errh.response.status_code
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting to Play.ht: {errc}")
        return jsonify({"status": "error", "message": f"Play.ht API Connection Error: {errc}"}), 500
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error calling Play.ht: {errt}")
        return jsonify({"status": "error", "message": f"Play.ht API Timeout Error: {errt}"}), 500
    except requests.exceptions.RequestException as err:
        print(f"An unexpected error occurred calling Play.ht: {err}")
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {err}"}), 500
    except Exception as e:
        print(f"An unexpected error occurred in webhook handler: {e}")
        return jsonify({"status": "error", "message": f"Internal server error: {e}"}), 500

@app.route('/')
def home():
    """Basic home route to confirm the app is running."""
    return "Play.ht Proxy is running! Send POST requests to /playht-webhook"

if __name__ == '__main__':
    # For local testing, use a port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

