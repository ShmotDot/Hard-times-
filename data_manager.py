
"""Centralized data management for game state"""

import json
import os
from typing import Dict, Any

class DataManager:
    """Manages loading and saving of game data"""
    
    def __init__(self):
        self.data_dir = "data"
        
    def load_json(self, filename: str) -> Dict[str, Any]:
        """Load JSON data file"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'r') as f:
            return json.load(f)
            
    def save_json(self, filename: str, data: Dict[str, Any]) -> None:
        """Save data to JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
