
"""
Save/Load system for Hard Times: Ottawa.
Handles saving and loading game state.
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

class SaveManager:
    def __init__(self):
        self.saves_dir = "saves"
        os.makedirs(self.saves_dir, exist_ok=True)
        
    def save_game(self, player, time_system, location_manager, event_manager) -> str:
        """Save current game state to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"save_{timestamp}.json"
        filepath = os.path.join(self.saves_dir, filename)
        
        save_data = {
            "timestamp": timestamp,
            "player": player.serialize(),
            "time": {
                "day": time_system.day,
                "hour": time_system.hour,
                "weather": time_system.weather,
                "temperature": time_system.temperature
            },
            "location": {
                "current": location_manager.current_location.name if location_manager.current_location else "Downtown"
            },
            "events": event_manager.serialize()
        }
        
        with open(filepath, 'w') as f:
            json.dump(save_data, f, indent=4)
            
        return filename
        
    def load_game(self, filename: str, player, time_system, location_manager, event_manager) -> bool:
        """Load game state from file."""
        filepath = os.path.join(self.saves_dir, filename)
        
        try:
            with open(filepath, 'r') as f:
                save_data = json.load(f)
                
            # Restore player state
            player.deserialize(save_data["player"])
            
            # Restore time system
            time_data = save_data["time"]
            time_system.day = time_data["day"]
            time_system.hour = time_data["hour"]
            time_system.weather = time_data["weather"]
            time_system.temperature = time_data["temperature"]
            
            # Restore location
            location_name = save_data["location"]["current"]
            location_manager.current_location = location_manager.get_location(location_name)
            
            # Restore events
            event_manager.deserialize(save_data["events"])
            
            return True
            
        except Exception as e:
            print(f"Error loading save file: {e}")
            return False
            
    def get_save_files(self) -> list:
        """Get list of available save files."""
        saves = []
        for filename in os.listdir(self.saves_dir):
            if filename.startswith("save_") and filename.endswith(".json"):
                filepath = os.path.join(self.saves_dir, filename)
                with open(filepath, 'r') as f:
                    save_data = json.load(f)
                saves.append({
                    "filename": filename,
                    "timestamp": save_data["timestamp"]
                })
        return saves
