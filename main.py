import os
import time
import json
import threading
import webbrowser
import queue
from datetime import datetime, timedelta
import requests
import webview
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, render_template_string, request, Response, send_from_directory

# Load environment variables from .env file
load_dotenv()

# Create a Flask app
app = Flask(__name__)

# Ensure templates are reloaded on every request
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Discord webhook configuration
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
if not DISCORD_WEBHOOK_URL:
    print("Warning: DISCORD_WEBHOOK_URL not found in .env file")

# Store for SSE clients
clients = []

# Define the HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Fisch Update Checker</title>
    <link rel="icon" type="image/x-icon" href="/favicon.ico">
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
        .button-container {
            margin-top: 20px;
            display: flex;
            gap: 10px;
        }
        .refresh-button {
            display: inline-block;
            padding: 10px 20px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            margin-top: 15px;
        }
        .refresh-button:hover {
            background-color: #0056b3;
        }
        .event-card {
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        .event-card.active {
            cursor: pointer;
            transition: transform 0.2s ease-in-out;
        }
        .event-card.active:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Fisch Update Checker</h1>
        <div class="update-info">
            {{ update_info|safe }}
        </div>
        <div class="button-container">
            <a href="javascript:void(0)" onclick="refreshUpdates()" class="refresh-button">Check for Updates</a>
        </div>
    </div>
    <script>
        // Set up SSE connection
        const eventSource = new EventSource('/events');
        
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.type === 'webhook') {
                updateContent(data.content);
            }
        };

        eventSource.onerror = function(error) {
            console.error("EventSource failed:", error);
            eventSource.close();
            // Try to reconnect after 5 seconds
            setTimeout(() => {
                window.location.reload();
            }, 5000);
        };

        function updateContent(content) {
            document.querySelector('.update-info').innerHTML = content;
            // Add click handlers to event cards after content update
            addEventCardHandlers();
        }

        function refreshUpdates() {
            fetch('/refresh-updates')
                .then(response => response.text())
                .then(data => {
                    updateContent(data);
                });
        }

        function launchGame() {
            fetch('/launch-game')
                .then(response => response.text())
                .then(data => console.log(data));
        }

        function addEventCardHandlers() {
            document.querySelectorAll('.event-card.active').forEach(card => {
                card.addEventListener('click', launchGame);
            });
        }

        function formatDateTime(timestamp) {
            const date = new Date(timestamp);
            const options = { 
                weekday: 'long',
                year: 'numeric', 
                month: 'long', 
                day: 'numeric',
                hour: '2-digit', 
                minute: '2-digit'
            };
            return date.toLocaleDateString(undefined, options);
        }

        function updateCountdowns() {
            document.querySelectorAll('.event-card').forEach(card => {
                const type = card.dataset.type;
                const timestamp = parseInt(card.dataset.timestamp);
                const countdownText = card.querySelector('.countdown-text');
                const dateText = card.querySelector('.date-text');
                
                if (type === 'recurring') {
                    const duration = parseInt(card.dataset.duration);
                    const period = parseInt(card.dataset.period);
                    const offset = parseInt(card.dataset.offset);
                    const showSeconds = card.dataset.showSeconds === 'true';
                    
                    // Calculate next occurrence
                    const now = Math.floor(Date.now() / 1000);
                    const cyclePosition = (now + offset) % period;
                    const timeUntilNext = period - cyclePosition;
                    const nextOccurrence = new Date((now + timeUntilNext) * 1000);
                    
                    // Format the countdown
                    const hours = Math.floor(timeUntilNext / 3600);
                    const minutes = Math.floor((timeUntilNext % 3600) / 60);
                    const seconds = timeUntilNext % 60;
                    
                    const timeStr = showSeconds ? 
                        `${hours}h ${minutes}m ${seconds}s` :
                        `${hours}h ${minutes}m`;
                        
                    countdownText.textContent = `Next in: ${timeStr}`;
                    dateText.textContent = `Next occurrence: ${formatDateTime(nextOccurrence)}`;
                    
                } else if (type === 'onetime') {
                    const eventTime = new Date(timestamp);
                    const now = new Date();
                    const diff = eventTime - now;
                    
                    if (diff > 0) {
                        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
                        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                        const seconds = Math.floor((diff % (1000 * 60)) / 1000);
                        
                        let timeStr = '';
                        if (days > 0) timeStr += `${days}d `;
                        timeStr += `${hours}h ${minutes}m ${seconds}s`;
                        
                        const status = card.querySelector('.countdown-text').textContent.includes('Ends') ? 'Ends' : 'Starts';
                        countdownText.textContent = `${status} in: ${timeStr}`;
                        dateText.textContent = `Event ${status.toLowerCase()} on: ${formatDateTime(eventTime)}`;
                    }
                }
            });
        }

        // Update countdowns every second
        setInterval(updateCountdowns, 1000);
        
        // Initial update
        updateCountdowns();

        // Add handlers when page loads
        document.addEventListener('DOMContentLoaded', addEventCardHandlers);
    </script>
</body>
</html>
"""

def check_for_updates():
    max_retries = 3
    initial_delay = 1

    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': os.getenv('USER_AGENT')
            }
            response = requests.get(os.getenv('WIKI_PAGE_URL'),
                                    headers=headers,
                                    timeout=10)

            if response.status_code == 429:
                # Get retry-after header or use exponential backoff
                delay = int(response.headers.get('Retry-After', initial_delay * (2 ** attempt)))
                next_retry = datetime.now().replace(microsecond=0) + timedelta(seconds=delay)

                if attempt == max_retries - 1:
                    return f"""
                        <div style='background-color: #fff0f0; padding: 15px; border-radius: 4px; margin-bottom: 15px;'>
                            <strong>Too Many Requests</strong><br>
                            We've made too many requests to the server.<br>
                            Please try again at {next_retry.strftime('%I:%M:%S %p')}.
                        </div>
                    """

                time.sleep(delay)
                continue

            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find both Current Events and Recurring Events sections
            events_sections = [
                ('Upcoming Content & Events', soup.find('div', id='Current_Events')),
                ('Recurring Events', soup.find('div', id='Recurring_Events'))
            ]

            update_html = ""
            for section_title, section in events_sections:
                if section:
                    # Get all countdown containers in this section
                    events_containers = section.find_next('div').find_all('div', class_='countdown-container')
                    
                    if events_containers:
                        update_html += f"<h2>{section_title}</h2>"
                        
                        for container in events_containers:
                            # Get event title
                            header = container.find('div', class_='countdown-header')
                            # Get countdown info
                            countdown_div = container.find('div', class_='countdown')
                            # Get event description
                            description = container.find('small')
                            
                            if header and countdown_div:
                                title = header.get_text().strip()
                                
                                # Handle both recurring and one-time events
                                if 'data-type' in countdown_div.attrs and countdown_div['data-type'] == 'recurring':
                                    # Recurring event
                                    timestamp = int(countdown_div.get('data-timestamp', 0))
                                    duration = int(countdown_div.get('data-duration', 0))
                                    period = int(countdown_div.get('data-period', 0))
                                    offset = int(countdown_div.get('data-period-offset', 0))
                                    show_seconds = countdown_div.get('data-show-seconds', 'false') == 'true'
                                    
                                    bg_color = "#fff0e8"  # Orange-ish for recurring events
                                    countdown_text = f"Recurring event (every {period//3600} hours)"
                                    
                                else:
                                    # One-time event
                                    timestamp = int(countdown_div.get('data-timestamp', 0))
                                    
                                    # Find if it's starting or ending
                                    prev_text = countdown_div.previous_sibling
                                    status_text = prev_text.strip() if prev_text else ""
                                    
                                    if timestamp > 1000000000000:  # If timestamp is in milliseconds
                                        event_time = datetime.fromtimestamp(timestamp/1000)
                                        time_str = event_time.strftime("%B %d, %Y at %I:%M %p")
                                        
                                        is_active = "Ends" in status_text
                                        bg_color = "#e8ffe8" if is_active else "#ffe8e8"
                                        countdown_text = f"{status_text} {time_str}"
                                    else:
                                        bg_color = "#f0f8ff"
                                        countdown_text = "Time not available"

                                desc = description.get_text().strip() if description else ""
                                active_class = ' active' if bg_color == "#e8ffe8" else ''
                                title_attr = ' title="Click to launch Fisch"' if bg_color == "#e8ffe8" else ''

                                update_html += f"""
                                    <div class="event-card{active_class}" style='background-color: {bg_color};'{title_attr}
                                        data-timestamp="{timestamp}"
                                        data-type="{'recurring' if 'data-type' in countdown_div.attrs else 'onetime'}"
                                        {f'data-duration="{duration}"' if 'data-type' in countdown_div.attrs else ''}
                                        {f'data-period="{period}"' if 'data-type' in countdown_div.attrs else ''}
                                        {f'data-offset="{offset}"' if 'data-type' in countdown_div.attrs else ''}
                                        {f'data-show-seconds="{str(show_seconds).lower()}"' if 'data-type' in countdown_div.attrs else ''}>
                                        <strong>{title}</strong><br>
                                        <span class="countdown-text" style='color: #666;'>{countdown_text}</span>
                                        <br><span class="date-text" style='color: #888; font-size: 0.9em;'></span>
                                        {f"<br><small>{desc}</small>" if desc else ""}
                                    </div>
                                """

            return update_html if update_html else "<div>No events found. Check the website for more information.</div>"
        except requests.RequestException as e:
            return f"Error checking for updates: Connection error - {str(e)}"
        except (AttributeError, ValueError) as e:
            return f"Error checking for updates: Failed to parse update information - {str(e)}"

def send_to_discord(message):
    """Send a message to Discord using the webhook"""
    try:
        payload = {
            "content": message,
            "username": "Fisch Update Checker"
        }
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except (requests.RequestException, requests.Timeout) as e:
        print(f"Error sending to Discord: {e}")
        return False

# Test the Discord connection on startup
def test_discord_connection():
    if send_to_discord("🎮 Fisch Update Checker is now online and monitoring for updates!"):
        print("Successfully connected to Discord!")
    else:
        print("Failed to connect to Discord. Please check your webhook URL.")

@app.route('/')
def home():
    update_info = check_for_updates()
    return render_template_string(HTML_TEMPLATE, update_info=update_info)

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
    return check_for_updates()

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
