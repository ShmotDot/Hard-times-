"""
Resource management system for Hard Times: Ottawa.
Handles all item-related functionality including inventory, item properties, and crafting.
"""
from enum import Enum
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import time
import json
import os
import random


class ItemCategory(Enum):
    """Categories of items in the game."""
    FOOD = "food"
    DRINK = "drink"
    CLOTHING = "clothing"
    MEDICINE = "medicine"
    TOOL = "tool"
    VALUABLE = "valuable"
    CRAFTING = "crafting"
    SHELTER = "shelter"
    DOCUMENT = "document"
    QUEST = "quest"
    MISC = "misc"


class ItemQuality(Enum):
    """Quality levels for items."""
    POOR = "poor"
    COMMON = "common"
    GOOD = "good"
    EXCELLENT = "excellent"


@dataclass
class ItemEffect:
    """Represents an effect that an item can have on player stats."""
    stat: str  # The stat affected (hunger, thirst, health, etc.)
    value: float  # The amount of change
    duration: int = 0  # Duration in hours (0 for instant)
    is_percentage: bool = False  # If True, value is a percentage of max stat


class Item:
    """Represents an item in the game."""
    
    def __init__(self, 
                 item_id: str, 
                 name: str, 
                 description: str, 
                 category: ItemCategory,
                 weight: float = 0.5, 
                 value: float = 0.0, 
                 durability: Optional[int] = None,
                 max_durability: Optional[int] = None,
                 quality: ItemQuality = ItemQuality.COMMON,
                 is_perishable: bool = False,
                 expiry_time: Optional[int] = None,
                 effects: Optional[List[ItemEffect]] = None,
                 tags: Optional[List[str]] = None):
        """Initialize an item."""
        self.item_id = item_id
        self.name = name
        self.description = description
        self.category = category
        self.weight = weight
        self.value = value
        self.durability = durability
        self.max_durability = max_durability
        self.quality = quality
        self.is_perishable = is_perishable
        self.expiry_time = expiry_time
        self.expiry_timestamp = None  # Set when added to inventory
        self.effects = effects or []
        self.tags = tags or []
        self.quantity = 1
    
    def use(self, player):
        """Use the item and apply its effects to the player."""
        # Check if item can be used (has durability left, not expired)
        if self.is_expired():
            return False, f"The {self.name} has expired and cannot be used."
        
        if self.durability is not None and self.durability <= 0:
            return False, f"The {self.name} is broken and cannot be used."
        
        # Apply effects to player
        applied_effects = []
        for effect in self.effects:
            if effect.stat == "hunger":
                player.satiety = min(100, player.satiety + effect.value)
                applied_effects.append(f"Increased satiety by {effect.value}")
            elif effect.stat == "satiety":  # Support for new satiety effects
                player.satiety = min(100, player.satiety + effect.value)
                applied_effects.append(f"Increased satiety by {effect.value}")
            elif effect.stat == "health":
                player.health = min(100, player.health + effect.value)
                applied_effects.append(f"Increased health by {effect.value}")
            elif effect.stat == "energy":
                player.energy = min(100, player.energy + effect.value)
                applied_effects.append(f"Increased energy by {effect.value}")
            elif effect.stat == "mental":
                player.mental = min(100, player.mental + effect.value)
                applied_effects.append(f"Improved mental health by {effect.value}")
        
        # Reduce durability if applicable
        if self.durability is not None:
            self.durability -= 1
            if self.durability <= 0:
                # Item is now broken
                return True, f"Used {self.name}. Effects: {', '.join(applied_effects)}. The item broke after use."
        
        return True, f"Used {self.name}. Effects: {', '.join(applied_effects)}"
    
    def is_expired(self):
        """Check if the item has expired."""
        if not self.is_perishable or self.expiry_timestamp is None:
            return False
        
        current_time = time.time()
        return current_time > self.expiry_timestamp
    
    def repair(self, amount=1):
        """Repair the item by the specified amount."""
        if self.durability is None or self.max_durability is None:
            return False
        
        if self.durability >= self.max_durability:
            return False
        
        self.durability = min(self.max_durability, self.durability + amount)
        return True


class Inventory:
    """Manages the player inventory system."""
    
    def __init__(self, max_weight=10.0):
        """Initialize the inventory."""
        self.items = {}  # item_id -> Item object
        self.quantities = {}  # item_id -> quantity
        self.max_weight = max_weight
    
    def add_item(self, item: Item, quantity=1):
        """Add an item to the inventory."""
        # Check if adding this item would exceed weight limit
        current_weight = self.get_total_weight()
        if current_weight + (item.weight * quantity) > self.max_weight:
            return False, "Your inventory is too heavy to carry this item."
        
        # If item is perishable, set expiry timestamp
        if item.is_perishable and item.expiry_time is not None:
            item.expiry_timestamp = time.time() + (item.expiry_time * 3600)  # Convert hours to seconds
        
        # Check if we already have this item
        if item.item_id in self.items:
            # Increase quantity
            current_quantity = self.quantities.get(item.item_id, 0)
            self.quantities[item.item_id] = current_quantity + quantity
        else:
            # Add new item to inventory
            self.items[item.item_id] = item
            self.quantities[item.item_id] = quantity
        
        return True, f"Added {quantity} {item.name} to inventory."
    
    def remove_item(self, item_id, quantity=1):
        """Remove an item from the inventory."""
        if item_id not in self.items:
            return False, "You don't have this item.", None
        
        item = self.items[item_id]
        current_quantity = self.quantities.get(item_id, 0)
        
        if current_quantity < quantity:
            return False, f"You only have {current_quantity} of this item.", None
        
        # Update quantity
        new_quantity = current_quantity - quantity
        if new_quantity <= 0:
            # Remove item completely
            removed_item = self.items[item_id]
            del self.items[item_id]
            del self.quantities[item_id]
            return True, f"Removed {quantity} {removed_item.name} from inventory.", removed_item
        else:
            # Update quantity
            self.quantities[item_id] = new_quantity
            return True, f"Removed {quantity} {item.name} from inventory.", item
    
    def get_item(self, item_id):
        """Get an item from the inventory."""
        return self.items.get(item_id)
    
    def get_items_by_category(self, category: ItemCategory):
        """Get all items of a specific category."""
        return [item for item in self.items.values() if item.category == category]
    
    def get_total_weight(self):
        """Get the total weight of all items in the inventory."""
        total = 0.0
        for item_id, item in self.items.items():
            quantity = self.quantities.get(item_id, 0)
            total += item.weight * quantity
        return round(total, 2)
    
    def get_total_value(self):
        """Get the total value of all items in the inventory."""
        return sum(item.value * self.quantities.get(item_id, 0) for item_id, item in self.items.items())
    
    def check_expiry(self):
        """Check and remove any expired items."""
        expired_items = []
        item_ids = list(self.items.keys())
        
        for item_id in item_ids:
            item = self.items[item_id]
            if item.is_perishable and item.is_expired():
                expired_items.append(item.name)
                del self.items[item_id]
                if item_id in self.quantities:
                    del self.quantities[item_id]
        
        return expired_items


class ResourceManager:
    """Manages game resources, item definitions, and crafting recipes."""
    
    def __init__(self, data_dir='data'):
        """Initialize the resource manager."""
        self.data_dir = data_dir
        self.items = {}  # Template items (not player inventory)
        self.crafting_recipes = []
        self.load_items()
        self.load_crafting_recipes()
    
    def load_items(self):
        """Load item definitions from the data file."""
        try:
            item_file = os.path.join(self.data_dir, 'items.json')
            if os.path.exists(item_file):
                with open(item_file, 'r') as f:
                    item_data = json.load(f)
                
                for item_info in item_data:
                    category = ItemCategory(item_info.get('category', 'misc'))
                    quality = ItemQuality(item_info.get('quality', 'common'))
                    
                    # Parse effects
                    effects = []
                    for effect_data in item_info.get('effects', []):
                        effects.append(ItemEffect(
                            stat=effect_data['stat'],
                            value=effect_data['value'],
                            duration=effect_data.get('duration', 0),
                            is_percentage=effect_data.get('is_percentage', False)
                        ))
                    
                    # Create the item
                    item = Item(
                        item_id=item_info['id'],
                        name=item_info['name'],
                        description=item_info['description'],
                        category=category,
                        weight=item_info.get('weight', 0.5),
                        value=item_info.get('value', 0.0),
                        durability=item_info.get('durability'),
                        max_durability=item_info.get('max_durability'),
                        quality=quality,
                        is_perishable=item_info.get('perishable', False),
                        expiry_time=item_info.get('expiry_time'),
                        effects=effects,
                        tags=item_info.get('tags', [])
                    )
                    
                    self.items[item.item_id] = item
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading item data: {e}")
    
    def load_crafting_recipes(self):
        """Load crafting recipes from the data file."""
        try:
            recipe_file = os.path.join(self.data_dir, 'crafting.json')
            if os.path.exists(recipe_file):
                with open(recipe_file, 'r') as f:
                    self.crafting_recipes = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading crafting data: {e}")
    
    def get_random_item_by_category(self, category):
        """Get a random item from a specific category."""
        category_items = [item for item in self.items.values() if item.category.value == category]
        if not category_items:
            return None
        return self.get_item_template(random.choice(category_items).item_id)
        
    def get_random_item(self, category=None, quality=None):
        """Get a random item, optionally filtering by category and quality.
        
        Args:
            category (ItemCategory, optional): Filter by item category
            quality (ItemQuality, optional): Filter by item quality
            
        Returns:
            Item or None: A random item or None if no matching items found
        """
        eligible_items = []
        
        for item_id, item in self.items.items():
            # Apply filters if specified
            if category and item.category != category:
                continue
            if quality and item.quality != quality:
                continue
            eligible_items.append(item_id)
            
        if not eligible_items:
            return None
            
        # Select a random item from eligible ones
        random_item_id = random.choice(eligible_items)
        return self.get_item_template(random_item_id)

    def get_item_template(self, item_id):
        """Get a fresh copy of an item template."""
        template = self.items.get(item_id)
        if template is None:
            return None
        
        # Create a new item with the same properties
        return Item(
            item_id=template.item_id,
            name=template.name,
            description=template.description,
            category=template.category,
            weight=template.weight,
            value=template.value,
            durability=template.durability,
            max_durability=template.max_durability,
            quality=template.quality,
            is_perishable=template.is_perishable,
            expiry_time=template.expiry_time,
            effects=[ItemEffect(e.stat, e.value, e.duration, e.is_percentage) for e in template.effects],
            tags=template.tags.copy()
        )
    
    def can_craft(self, recipe_id, inventory):
        """Check if player can craft a recipe with their current inventory."""
        recipe = None
        for r in self.crafting_recipes:
            if r.get('id') == recipe_id:
                recipe = r
                break
        
        if recipe is None:
            return False, ["Recipe not found"]
        
        missing_items = []
        if 'ingredients' in recipe:
            for ingredient in recipe['ingredients']:
                item_id = ingredient.get('id')
                quantity = ingredient.get('quantity', 1)
                
                inventory_item = inventory.get_item(item_id)
                inventory_quantity = inventory.quantities.get(item_id, 0) if inventory_item else 0
                
                if inventory_item is None or inventory_quantity < quantity:
                    missing_quantity = quantity - inventory_quantity
                    template = self.get_item_template(item_id)
                    item_name = template.name if template else item_id
                    missing_items.append(f"{item_name} (need {missing_quantity} more)")
        
        return len(missing_items) == 0, missing_items
    
    def craft_item(self, recipe_id, inventory):
        """Craft an item using the player inventory."""
        # First check if we can craft (have all ingredients)
        can_craft, missing_items = self.can_craft(recipe_id, inventory)
        if not can_craft:
            return False, f"Cannot craft: missing {', '.join(missing_items)}", None
        
        # Find the recipe
        recipe = None
        for r in self.crafting_recipes:
            if r.get('id') == recipe_id:
                recipe = r
                break
        
        if recipe is None:
            return False, "Recipe not found", None
            
        # Remove ingredients from inventory
        if 'ingredients' in recipe:
            for ingredient in recipe['ingredients']:
                item_id = ingredient.get('id')
                quantity = ingredient.get('quantity', 1)
                success, message, _ = inventory.remove_item(item_id, quantity)
                if not success:
                    # This shouldn't happen since we checked with can_craft, but just in case
                    return False, "Error removing ingredients from inventory", None
        
        # Create the crafted item
        if 'result' in recipe:
            result = recipe['result']
            result_item_id = result.get('id')
            result_quantity = result.get('quantity', 1)
            
            crafted_item = self.get_item_template(result_item_id)
            if crafted_item is None:
                return False, f"Error: result item {result_item_id} not found in item templates", None
            
            # Add the crafted item to inventory
            success, message = inventory.add_item(crafted_item, result_quantity)
            if not success:
                # Return the ingredients if crafting fails due to inventory constraints
                if 'ingredients' in recipe:
                    for ingredient in recipe['ingredients']:
                        item_id = ingredient.get('id')
                        quantity = ingredient.get('quantity', 1)
                        template = self.get_item_template(item_id)
                        if template:
                            inventory.add_item(template, quantity)
                return False, message, None
            
            return True, f"Successfully crafted {result_quantity} {crafted_item.name}", crafted_item
        else:
            return False, "Invalid recipe format: no result specified", None