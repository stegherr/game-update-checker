import time
import webview
import threading
from flask import Flask, render_template_string
import requests
from bs4 import BeautifulSoup
import webbrowser

# Create a Flask app
app = Flask(__name__)

# Define the HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Fisch Update Checker</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px;
            background-color: #f5f5f5;
        }
        h1 { 
            color: #333;
            border-bottom: 2px solid #ddd;
            padding-bottom: 10px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .update-info {
            margin: 20px 0;
            padding: 15px;
            background: #f0f8ff;
            border-radius: 4px;
        }
        .button {
            display: inline-block;
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            margin-top: 15px;
        }
        .button:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Fisch Update Checker</h1>
        <div class="update-info">
            <h2>Update Information</h2>
            {{ update_info|safe }}
        </div>
        <a href="javascript:void(0)" onclick="launchGame()" class="button">Launch Fisch</a>
    </div>
    <script>
        function launchGame() {
            fetch('/launch-game')
                .then(response => response.text())
                .then(data => console.log(data));
        }
    </script>
</body>
</html>
"""

def check_for_updates():
    try:
        response = requests.get('https://fischipedia.org/wiki/Fisch_Wiki')
        soup = BeautifulSoup(response.text, 'html.parser')
        # You might need to adjust the selector based on the actual website structure
        update_info = "Unable to fetch update information. Please check the website directly."
        return update_info
    except Exception as e:
        return f"Error checking for updates: {str(e)}"

@app.route('/')
def home():
    update_info = check_for_updates()
    return render_template_string(HTML_TEMPLATE, update_info=update_info)

@app.route('/launch-game')
def launch_game():
    # Replace this URL with the actual Roblox game URL for Fisch
    game_url = "roblox://placeId=16732694052"
    webbrowser.open(game_url)
    return "Launching game..."

def run_flask():
    app.run(debug=False, port=5000)

def create_window():
    # Create a webview window
    webview.create_window('Fisch Update Checker', 'http://localhost:5000', width=800, height=600)
    webview.start()

if __name__ == "__main__":
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Give Flask a moment to start
    time.sleep(1)
    
    # Start the webview window
    create_window()