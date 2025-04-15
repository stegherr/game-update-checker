"""Route handlers for the web application."""
import os
import time
# import queue
import threading
import webbrowser
import webview
from flask import render_template, send_from_directory  #, Response, request
from app.services.update_service import UpdateService
# from app.services.event_service import EventService

def register_routes(app):
    """Register all routes for the Flask app."""
    # Store for SSE clients
    # clients = []

    @app.route('/')
    def home():
        update_info = UpdateService.check_for_updates()
        return render_template('index.html', update_info=update_info)

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, '../static'),
                                  'favicon.ico', mimetype='image/vnd.microsoft.icon')

    @app.route('/static/<path:path>')
    def send_static(path):
        return send_from_directory('static', path)

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

    # @app.route('/events')
    # def events():
    #     def generate():
    #         # Create a queue for this client
    #         message_queue = queue.Queue()
    #         clients.append(message_queue)
    #         try:
    #             while True:
    #                 message = message_queue.get()
    #                 yield f"data: {message}\n\n"
    #         except GeneratorExit:
    #             clients.remove(message_queue)

    #     return Response(generate(), mimetype='text/event-stream')

    # @app.route('/app-webhook', methods=['POST'])
    # def app_webhook():
    #     try:
    #         # Parse the incoming JSON payload
    #         data = request.json

    #         # Extract relevant information from the payload
    #         if 'content' in data:
    #             message_content = data['content']
    #             # Create HTML content for the update
    #             update_html = f"""
    #                 <div style='background-color: #f0f8ff; padding: 15px; border-radius: 4px; margin-bottom: 15px;'>
    #                     <strong>Discord Update:</strong><br>
    #                     {message_content}
    #                 </div>
    #             """
    #             # Send update to all connected clients
    #             EventService.send_update_to_clients(update_html)
    #             # Send a confirmation back to Discord
    #             # send_to_discord("✅ Update received and displayed in the app!")
    #             return "Update sent", 200
    #         else:
    #             return "Invalid payload", 400
    #     except (ValueError, KeyError, requests.RequestException) as e:
    #         return f"Error processing webhook: {str(e)}", 500
