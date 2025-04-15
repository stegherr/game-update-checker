import json
import os
from datetime import datetime
from app.services.update_service import UpdateService

def main():
    """Update the event data JSON file"""
    try:
        # Get updates using existing service
        updates = UpdateService.check_for_updates()
        
        # Format data for JSON
        data = {
            'lastUpdate': datetime.now().isoformat(),
            'content': updates
        }
        
        # Ensure data directory exists
        os.makedirs('docs/data', exist_ok=True)
        
        # Save to JSON file
        with open('docs/data/updates.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print("Successfully updated event data")
        return True
            
    except Exception as e:
        print(f"Error updating event data: {str(e)}")
        return False

if __name__ == '__main__':
    main()