import os
import requests
from flask import Flask, request, jsonify
import re # Import the regular expression module

app = Flask(__name__)

# --- Configuration (Read from Environment Variables) ---
PLAYHT_USER_ID = os.environ.get("PLAYHT_USER_ID")
PLAYHT_SECRET_KEY = os.environ.get("PLAYHT_SECRET_KEY")
PLAYHT_AGENT_ID = os.environ.get("PLAYHT_AGENT_ID")

# Play.ht API endpoint for making calls
PLAYHT_API_URL = "https://api.play.ht/v2/calls"

def format_phone_number_e164(phone_number_str):
    """
    Formats a phone number string into E.164 format (+[country code][number]).
    Assumes US numbers if no country code is present.
    """
    if not phone_number_str:
        return None

    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone_number_str)

    # If it starts with a country code (e.g., +1), keep it
    if phone_number_str.startswith('+'):
        return '+' + digits_only
    
    # If it's a US number and doesn't start with +, prepend +1
    # This is a basic assumption; for international leads, you'd need more sophisticated logic
    if len(digits_only) == 10: # Assumes 10-digit US number
        return '+1' + digits_only
    elif len(digits_only) == 11 and digits_only.startswith('1'): # Assumes 11-digit US number starting with 1
        return '+' + digits_only
    
    # Fallback: if it's not clearly E.164 or a 10/11 digit US number, just prepend +
    # This might not be robust for all international numbers without country code
    return '+' + digits_only


@app.route('/playht-webhook', methods=['POST'])
def handle_playht_webhook():
    """
    Receives lead data from Zapier, formats it, and sends it to Play.ht's API.
    """
    if not request.is_json:
        print("Error: Request must be JSON")
        return jsonify({"error": "Request must be JSON"}), 400

    zapier_data = request.get_json()
    print(f"Received data from Zapier: {zapier_data}")

    # Extract name and phone number from Zapier's payload
    customer_name = zapier_data.get('name')
    raw_phone_number = zapier_data.get('phoneNumber')

    if not customer_name or not raw_phone_number:
        print("Error: Missing 'name' or 'phoneNumber' in request from Zapier")
        return jsonify({"error": "Missing 'name' or 'phoneNumber' in request"}), 400

    # Format the phone number to E.164
    formatted_phone_number = format_phone_number_e164(raw_phone_number)
    if not formatted_phone_number:
        print(f"Error: Could not format phone number '{raw_phone_number}' to E.164")
        return jsonify({"error": f"Invalid phone number format: {raw_phone_number}"}), 400

    # Construct the payload for Play.ht API
    playht_payload = {
        "agentId": PLAYHT_AGENT_ID,
        "phoneNumber": formatted_phone_number, # Use the formatted number
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

    print(f"Attempting to call Play.ht with payload: {playht_payload}")
    print(f"Headers (excluding secret key for logging): X-User-ID={PLAYHT_USER_ID}")

    try:
        # Make the POST request to Play.ht API
        response = requests.post(PLAYHT_API_URL, json=playht_payload, headers=playht_headers)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

        playht_response_data = response.json()
        print(f"Successfully sent call request to Play.ht: {playht_response_data}")
        return jsonify({"status": "success", "playht_response": playht_response_data}), 200

    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error calling Play.ht: {errh}")
        print(f"Play.ht Error Details: {errh.response.text}") # Print the actual error from Play.ht
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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
