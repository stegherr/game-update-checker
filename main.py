import os
import time
import json
import threading
import webbrowser
import queue
import requests
import webview
from dotenv import load_dotenv
from flask import Flask, render_template, request, Response, send_from_directory
from app.services.update_service import UpdateService

# Load environment variables from .env file
load_dotenv()

# Create a Flask app
app = Flask(__name__, template_folder='templates')

# Ensure templates are reloaded on every request
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Store for SSE clients
clients = []

@app.route('/')
def home():
    update_info = UpdateService.check_for_updates()
    return render_template('index.html', update_info=update_info)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/launch-game')
def launch_game():
    game_url = "roblox://placeId=16732694052"
    webbrowser.open(game_url)

    # Close the app after launching the game
    if webview.windows:
        def graceful_shutdown():
            # Destroy webview window first
            webview.windows[0].destroy()
            # Then exit the process
            time.sleep(0.5)
            os._exit(0)

        threading.Thread(target=graceful_shutdown).start()

    return "Launching game..."

@app.route('/refresh-updates')
def refresh_updates():
    return UpdateService.check_for_updates()

def send_update_to_clients(content):
    message = json.dumps({
        'type': 'webhook',
        'content': content
    })
    for client in clients[:]:
        try:
            client.put(message)
        except queue.Empty:
            clients.remove(client)

@app.route('/events')
def events():
    def generate():
        # Create a queue for this client
        message_queue = queue.Queue()
        clients.append(message_queue)
        try:
            while True:
                message = message_queue.get()
                yield f"data: {message}\n\n"
        except GeneratorExit:
            clients.remove(message_queue)

    return Response(generate(), mimetype='text/event-stream')

@app.route('/app-webhook', methods=['POST'])
def app_webhook():
    try:
        # Parse the incoming JSON payload
        data = request.json

        # Extract relevant information from the payload
        if 'content' in data:
            message_content = data['content']
            # Create HTML content for the update
            update_html = f"""
                <div style='background-color: #f0f8ff; padding: 15px; border-radius: 4px; margin-bottom: 15px;'>
                    <strong>Discord Update:</strong><br>
                    {message_content}
                </div>
            """
            # Send update to all connected clients
            send_update_to_clients(update_html)
            # Send a confirmation back to Discord
            # send_to_discord("✅ Update received and displayed in the app!")
            return "Update sent", 200
        else:
            return "Invalid payload", 400
    except (ValueError, KeyError, requests.RequestException) as e:
        return f"Error processing webhook: {str(e)}", 500

def run_flask():
    app.run(debug=False, port=5000)

def create_window():
    # Create a webview window
    webview.create_window('Fisch Update Checker', 'http://localhost:5000', width=800, height=710)
    webview.start()

if __name__ == "__main__":
    # Test Discord connection before starting the app
    # test_discord_connection()

    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Give Flask a moment to start
    time.sleep(1)

    # Start the webview window
    create_window()
