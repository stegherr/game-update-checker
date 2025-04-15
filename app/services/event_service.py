"""Event service module for handling events and notifications."""
import json
import queue

# Store for SSE clients
clients = []

class EventService:
    """Handles events and notifications for the application."""
    def send_update_to_clients(self, content):
        """Send updates to all connected clients."""
        message = json.dumps({
            'type': 'webhook',
            'content': content
        })
        for client in clients[:]:
            try:
                client.put(message)
            except queue.Empty:
                clients.remove(client)
