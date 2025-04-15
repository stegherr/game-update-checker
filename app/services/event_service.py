"""Event service module for handling events and notifications."""
import json
import queue

class EventService:
    """Handles events and notifications for the application."""
    def __init__(self):
        self.clients = []

    def add_client(self, client_queue):
        """Add a new client queue."""
        self.clients.append(client_queue)

    def remove_client(self, client_queue):
        """Remove a client queue."""
        if client_queue in self.clients:
            self.clients.remove(client_queue)

    def send_update_to_clients(self, content):
        """Send updates to all connected clients."""
        message = json.dumps({
            'type': 'webhook',
            'content': content
        })
        for client in self.clients[:]:
            try:
                client.put(message)
            except queue.Empty:
                self.clients.remove(client)
