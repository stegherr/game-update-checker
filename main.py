"""Main application file for Fisch Update Checker"""
import time
import threading
import webview
from app import create_app
# from app.services.discord_service import DiscordService

app = create_app()

def run_flask():
    """ Run the Flask app """
    app.run(debug=False, port=app.config['PORT'])

def create_window():
    """ Create a webview window """
    webview.create_window('Fisch Update Checker', f'http://localhost:{app.config["PORT"]}',
                          width=800, height=710)
    webview.start()

if __name__ == "__main__":
    # Test Discord connection before starting the app
    # DiscordService.test_connection()

    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Give Flask a moment to start
    time.sleep(1)

    # Start the webview window
    create_window()
