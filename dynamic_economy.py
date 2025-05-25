"""
Dynamic Economy System for Hard Times: Ottawa.
Handles fluctuating prices, location economy, and market events.
"""
import random
import math
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass
import json

@dataclass
class Item:
    """Represents a purchasable or sellable item in the economy."""
    id: str
    name: str
    description: str
    base_price: float
    category: str
    tags: List[str]
    weight: float = 0.5
    durability: int = 100
    consumable: bool = False
    effects: Dict[str, Any] = None
    rarity: float = 1.0  # 1.0 is normal, higher is rarer
    legal: bool = True
    seasonal_demand: Dict[str, float] = None  # Season -> demand multiplier

    def __post_init__(self):
        if self.effects is None:
            self.effects = {}
        if self.seasonal_demand is None:
            self.seasonal_demand = {
                "winter": 1.0,
                "spring": 1.0,
                "summer": 1.0,
                "fall": 1.0
            }


class Merchant:
    """Represents a merchant or shop in the game."""
    
    def __init__(self, merchant_id: str, name: str, location: str, 
                merchant_type: str, faction: str = None):
        self.id = merchant_id
        self.name = name
        self.location = location
        self.type = merchant_type  # "regular", "black_market", "specialized", etc.
        self.faction = faction
        self.inventory = {}  # item_id -> quantity
        self.price_modifiers = {}  # item_id -> specific modifier
        self.base_markup = 1.2  # 20% markup
        self.base_buy_discount = 0.5  # 50% of value when buying from player
        self.reputation_discount_factor = 0.05  # 5% discount per 10 points of reputation
        self.price_history = {}  # item_id -> list of recent prices
        self.haggle_difficulty = 50  # 0-100, higher is harder
        self.specialty_categories = []  # Categories this merchant specializes in
        self.banned_items = []  # Items this merchant won't buy/sell
        self.daily_restock = {}  # item_id -> daily restock amount
        self.special_offers = []  # Current special deals
        self.last_restock_day = 0
        
    def set_inventory(self, items: Dict[str, int]):
        """Initialize the merchant's inventory.
        
        Args:
            items: Dictionary of item_id -> quantity
        """
        self.inventory = items.copy()
        
    def calculate_sell_price(self, item_id: str, item_data: Item, economy_system, 
                            player_reputation: int = 0) -> float:
        """Calculate the price to sell an item to a player.
        
        Args:
            item_id: ID of the item
            item_data: Item object with base data
            economy_system: Economy system for global modifiers
            player_reputation: Player's reputation with merchant's faction
            
        Returns:
            float: Sell price
        """
        # Start with base price
        price = item_data.base_price
        
        # Apply merchant's specific modifiers
        price *= self.base_markup
        if item_id in self.price_modifiers:
            price *= self.price_modifiers[item_id]
            
        # Apply item rarity modifier
        price *= item_data.rarity
        
        # Apply location modifier
        location_mod = economy_system.get_location_modifier(self.location)
        price *= location_mod
        
        # Apply global economy modifier
        global_mod = economy_system.get_global_modifier()
        price *= global_mod
        
        # Apply category demand modifier
        demand_mod = economy_system.get_category_demand(item_data.category)
        price *= demand_mod
        
        # Apply seasonal modifier if applicable
        season = economy_system.current_season
        if season in item_data.seasonal_demand:
            price *= item_data.seasonal_demand[season]
            
        # Apply faction reputation discount
        reputation_discount = 1.0 - (player_reputation * self.reputation_discount_factor / 10)
        reputation_discount = max(0.6, reputation_discount)  # Cap at 40% discount
        price *= reputation_discount
        
        # Apply any active events
        event_mod = economy_system.get_event_modifier(item_id, item_data.category)
        price *= event_mod
        
        # Apply scarcity modifier
        quantity = self.inventory.get(item_id, 0)
        if quantity <= 1:
            price *= 1.5  # 50% markup for last item
        elif quantity <= 3:
            price *= 1.2  # 20% markup for scarce items
            
        # Apply random daily fluctuation (±5%)
        daily_fluctuation = random.uniform(0.95, 1.05)
        price *= daily_fluctuation
        
        # Round to nearest cent and ensure minimum price
        price = max(0.25, round(price, 2))
        
        # Update price history
        if item_id not in self.price_history:
            self.price_history[item_id] = []
        self.price_history[item_id].append(price)
        if len(self.price_history[item_id]) > 10:
            self.price_history[item_id].pop(0)
            
        return price
    
    def calculate_buy_price(self, item_id: str, item_data: Item, economy_system,
                           player_reputation: int = 0) -> float:
        """Calculate the price to buy an item from a player.
        
        Args:
            item_id: ID of the item
            item_data: Item object with base data
            economy_system: Economy system for global modifiers
            player_reputation: Player's reputation with merchant's faction
            
        Returns:
            float: Buy price
        """
        # First calculate theoretical sell price
        sell_price = self.calculate_sell_price(item_id, item_data, economy_system, player_reputation)
        
        # Apply buy discount
        buy_price = sell_price * self.base_buy_discount
        
        # Adjust based on demand
        demand_mod = economy_system.get_category_demand(item_data.category)
        if demand_mod > 1.2:  # High demand
            buy_price *= 1.2
        elif demand_mod < 0.8:  # Low demand
            buy_price *= 0.8
            
        # Adjust if merchant specializes in this category
        if item_data.category in self.specialty_categories:
            buy_price *= 1.2
            
        # Adjust based on current inventory
        quantity = self.inventory.get(item_id, 0)
        if quantity > 10:  # Already has plenty
            buy_price *= 0.7
        elif quantity == 0:  # Doesn't have any
            buy_price *= 1.15
            
        # Adjust for reputation - better reputation means better buy prices
        rep_bonus = 1.0 + (player_reputation * self.reputation_discount_factor / 15)
        rep_bonus = min(1.3, rep_bonus)  # Cap at 30% bonus
        buy_price *= rep_bonus
        
        # Round to nearest cent
        buy_price = max(0.10, round(buy_price, 2))
        
        return buy_price
    
    def is_willing_to_buy(self, item_id: str, item_data: Item) -> bool:
        """Check if the merchant is willing to buy an item.
        
        Args:
            item_id: ID of the item
            item_data: Item object with base data
            
        Returns:
            bool: True if willing to buy
        """
        # Check if item is banned
        if item_id in self.banned_items or item_data.category in self.banned_items:
            return False
            
        # Check if legal merchant refusing illegal items
        if self.type == "regular" and not item_data.legal:
            return False
            
        # Check if inventory is full (arbitrary limit)
        total_items = sum(self.inventory.values())
        if total_items > 200:  # Arbitrary limit
            return False
            
        return True
    
    def haggle(self, player_charisma: int, item_value: float, is_buying: bool) -> float:
        """Attempt to haggle for a better price.
        
        Args:
            player_charisma: Player's charisma/social skill (0-100)
            item_value: Base value of item
            is_buying: True if player is buying, False if selling
            
        Returns:
            float: Price modification percentage (1.0 means no change)
        """
        # Base haggle chance
        base_chance = 30 + (player_charisma * 0.5)
        
        # Adjust for haggle difficulty
        success_chance = base_chance - self.haggle_difficulty
        
        # Cap success chance
        success_chance = max(5, min(95, success_chance))
        
        # Determine success
        if random.randint(1, 100) <= success_chance:
            # Success - calculate amount
            base_modifier = 0.05 + (player_charisma * 0.002)  # 5-25% change
            
            if is_buying:
                # When buying, success means lower price
                return 1.0 - min(0.25, base_modifier)
            else:
                # When selling, success means higher price
                return 1.0 + min(0.3, base_modifier)
        else:
            # Failure - slight penalty
            if is_buying:
                # When buying, failure means higher price
                return 1.05
            else:
                # When selling, failure means lower price
                return 0.95
    
    def restock(self, current_day: int, economy_system):
        """Restock items if a new day has passed.
        
        Args:
            current_day: Current game day
            economy_system: The economy system
        """
        if current_day <= self.last_restock_day:
            return
            
        # Restock daily items
        for item_id, amount in self.daily_restock.items():
            # Apply some randomness to restock amount
            actual_amount = max(0, int(amount * random.uniform(0.7, 1.3)))
            self.inventory[item_id] = self.inventory.get(item_id, 0) + actual_amount
            
        # Generate occasional special offers
        if random.random() < 0.3:  # 30% chance each day
            self._generate_special_offers(economy_system)
            
        self.last_restock_day = current_day
    
    def _generate_special_offers(self, economy_system):
        """Generate special offers with discounts or rare items.
        
        Args:
            economy_system: The economy system
        """
        self.special_offers = []
        
        # Get all possible items from economy system
        all_items = economy_system.get_all_items()
        
        # Filter to items this merchant might carry
        potential_items = []
        for item_id, item in all_items.items():
            if (item.category in self.specialty_categories and 
                item_id not in self.banned_items and
                item.legal == (self.type == "regular")):
                potential_items.append((item_id, item))
                
        # Choose up to 3 special offers if we have enough potential items
        num_offers = min(3, len(potential_items))
        if num_offers > 0:
            chosen = random.sample(potential_items, num_offers)
            
            for item_id, item in chosen:
                # Determine special offer type
                offer_type = random.choice(["discount", "bulk", "rare"])
                
                if offer_type == "discount":
                    # Discount offer (10-30% off)
                    discount = random.uniform(0.1, 0.3)
                    self.special_offers.append({
                        "item_id": item_id,
                        "type": "discount",
                        "value": discount,
                        "quantity": 1
                    })
                    
                elif offer_type == "bulk":
                    # Bulk deal (buy 2-5, get discount)
                    quantity = random.randint(2, 5)
                    discount = random.uniform(0.15, 0.35)
                    self.special_offers.append({
                        "item_id": item_id,
                        "type": "bulk",
                        "value": discount,
                        "quantity": quantity
                    })
                    
                elif offer_type == "rare":
                    # Rare item (limited quantity)
                    quantity = random.randint(1, 3)
                    self.special_offers.append({
                        "item_id": item_id,
                        "type": "rare",
                        "value": 0,
                        "quantity": quantity
                    })
                    # Add to inventory if not already there
                    self.inventory[item_id] = self.inventory.get(item_id, 0) + quantity


class EconomicEvent:
    """Represents an economic event affecting prices and availability."""
    
    def __init__(self, event_id: str, name: str, description: str, duration: int):
        self.id = event_id
        self.name = name
        self.description = description
        self.duration = duration  # In days
        self.remaining_duration = duration
        self.active = True
        self.affected_categories = []  # Categories affected by this event
        self.affected_items = []  # Specific items affected
        self.price_modifiers = {}  # category/item_id -> modifier
        self.availability_modifiers = {}  # category/item_id -> modifier
        self.location_specific = None  # If None, affects all locations
        self.news_headline = None  # News headline for event
        
    def affects_item(self, item_id: str, category: str) -> bool:
        """Check if this event affects a specific item.
        
        Args:
            item_id: Item ID to check
            category: Item category
            
        Returns:
            bool: True if affected
        """
        return (item_id in self.affected_items or 
                category in self.affected_categories)
    
    def get_price_modifier(self, item_id: str, category: str) -> float:
        """Get price modifier for an item.
        
        Args:
            item_id: Item ID
            category: Item category
            
        Returns:
            float: Price modifier (1.0 means no change)
        """
        # Check for specific item modifier
        if item_id in self.price_modifiers:
            return self.price_modifiers[item_id]
            
        # Check for category modifier
        if category in self.price_modifiers:
            return self.price_modifiers[category]
            
        # Default - no change
        return 1.0
    
    def get_availability_modifier(self, item_id: str, category: str) -> float:
        """Get availability modifier for an item.
        
        Args:
            item_id: Item ID
            category: Item category
            
        Returns:
            float: Availability modifier (1.0 means no change)
        """
        # Check for specific item modifier
        if item_id in self.availability_modifiers:
            return self.availability_modifiers[item_id]
            
        # Check for category modifier
        if category in self.availability_modifiers:
            return self.availability_modifiers[category]
            
        # Default - no change
        return 1.0
    
    def update(self):
        """Update event state - call once per day."""
        if self.active:
            self.remaining_duration -= 1
            if self.remaining_duration <= 0:
                self.active = False
    
    def get_news(self) -> Optional[str]:
        """Get news headline for this event if available.
        
        Returns:
            str or None: News headline
        """
        if self.news_headline:
            return self.news_headline
            
        # Generate basic news if none provided
        if self.remaining_duration == self.duration:  # First day
            affected = []
            if self.affected_categories:
                affected = self.affected_categories
            elif self.affected_items:
                affected = ["various goods"]
                
            if affected:
                affected_str = ", ".join(affected)
                # Check if prices are going up or down
                price_direction = "rise" if next(iter(self.price_modifiers.values())) > 1.0 else "fall"
                return f"{self.name}: Prices of {affected_str} expected to {price_direction}."
            
        return None


class DynamicEconomySystem:
    """Manages the game's economy including prices, merchants, and economic events."""
    
    def __init__(self):
        self.merchants = {}
        self.items = {}
        self.economic_events = []
        self.global_economy = 1.0  # Global economic multiplier (1.0 is baseline)
        self.category_demand = {}  # Category -> demand multiplier
        self.location_modifiers = {}  # Location -> economic multiplier
        self.black_market_items = []  # Items only available on black market
        self.current_season = "fall"  # default season
        self.current_day = 1
        self.price_histories = {}  # item_id -> list of price points
        
        # Load data
        self._load_items()
        self._load_merchants()
        self._initialize_economy()
        
    def _load_items(self, file_path='data/items.json'):
        """Load item data from JSON file."""
        try:
            with open(file_path, 'r') as f:
                items_data = json.load(f)
                
            for item_id, data in items_data.items():
                self.items[item_id] = Item(
                    id=item_id,
                    name=data.get("name", "Unknown Item"),
                    description=data.get("description", ""),
                    base_price=data.get("price", 1.0),
                    category=data.get("category", "misc"),
                    tags=data.get("tags", []),
                    weight=data.get("weight", 0.5),
                    durability=data.get("durability", 100),
                    consumable=data.get("consumable", False),
                    effects=data.get("effects", {}),
                    rarity=data.get("rarity", 1.0),
                    legal=data.get("legal", True),
                    seasonal_demand=data.get("seasonal_demand", None)
                )
                
                # Track black market items
                if not data.get("legal", True):
                    self.black_market_items.append(item_id)
                    
        except FileNotFoundError:
            print(f"Items file not found at {file_path}")
            self._create_default_items()
        except Exception as e:
            print(f"Error loading items: {e}")
            self._create_default_items()
    
    def _create_default_items(self):
        """Create basic default items."""
        # Basic food items
        self.items["food_sandwich"] = Item(
            id="food_sandwich",
            name="Sandwich",
            description="A basic sandwich. Filling but not nutritious.",
            base_price=5.0,
            category="food",
            tags=["food", "consumable"],
            consumable=True,
            effects={"hunger": 30},
            seasonal_demand={
                "winter": 1.0,
                "spring": 1.0,
                "summer": 0.9,
                "fall": 1.1
            }
        )
        
        self.items["food_canned_beans"] = Item(
            id="food_canned_beans",
            name="Canned Beans",
            description="Non-perishable food source. Lasts a long time.",
            base_price=2.5,
            category="food",
            tags=["food", "consumable", "non-perishable"],
            consumable=True,
            effects={"hunger": 25},
            seasonal_demand={
                "winter": 1.2,
                "spring": 1.0,
                "summer": 0.9,
                "fall": 1.0
            }
        )
        
        # Basic drink
        self.items["drink_water_bottle"] = Item(
            id="drink_water_bottle",
            name="Water Bottle",
            description="Clean drinking water in a plastic bottle.",
            base_price=2.0,
            category="drink",
            tags=["drink", "consumable"],
            consumable=True,
            effects={"thirst": 40},
            seasonal_demand={
                "winter": 0.9,
                "spring": 1.0,
                "summer": 1.5,
                "fall": 1.0
            }
        )
        
        # Clothing
        self.items["clothing_socks"] = Item(
            id="clothing_socks",
            name="Pair of Socks",
            description="Clean, warm socks. Essential for foot health.",
            base_price=5.0,
            category="clothing",
            tags=["clothing", "warmth"],
            effects={"warmth": 10},
            seasonal_demand={
                "winter": 1.5,
                "spring": 1.0,
                "summer": 0.7,
                "fall": 1.2
            }
        )
        
        # Survival item
        self.items["sleeping_bag"] = Item(
            id="sleeping_bag",
            name="Sleeping Bag",
            description="Provides warmth and comfort when sleeping outdoors.",
            base_price=25.0,
            category="survival",
            tags=["survival", "warmth", "shelter"],
            weight=2.0,
            effects={"sleep_quality": 20, "warmth": 30},
            seasonal_demand={
                "winter": 2.0,
                "spring": 1.2,
                "summer": 0.8,
                "fall": 1.5
            }
        )
        
        # Illegal item example
        self.items["narcotic_painkillers"] = Item(
            id="narcotic_painkillers",
            name="Prescription Painkillers",
            description="Strong painkillers without a prescription.",
            base_price=30.0,
            category="medical",
            tags=["medical", "drug", "illegal", "consumable"],
            consumable=True,
            effects={"pain": -40, "mental": 15, "health": -5},
            rarity=2.0,
            legal=False,
            seasonal_demand={
                "winter": 1.2,
                "spring": 1.0,
                "summer": 1.0,
                "fall": 1.1
            }
        )
        
        # Add to black market list
        self.black_market_items.append("narcotic_painkillers")
        
    def _load_merchants(self, file_path='data/merchants.json'):
        """Load merchant data from JSON file."""
        try:
            with open(file_path, 'r') as f:
                merchants_data = json.load(f)
                
            for merchant_id, data in merchants_data.items():
                merchant = Merchant(
                    merchant_id=merchant_id,
                    name=data.get("name", "Unknown Merchant"),
                    location=data.get("location", "Downtown"),
                    merchant_type=data.get("type", "regular"),
                    faction=data.get("faction", None)
                )
                
                # Set merchant properties
                merchant.base_markup = data.get("markup", 1.2)
                merchant.base_buy_discount = data.get("buy_discount", 0.5)
                merchant.haggle_difficulty = data.get("haggle_difficulty", 50)
                merchant.specialty_categories = data.get("specialties", [])
                merchant.banned_items = data.get("banned_items", [])
                
                # Set inventory
                inventory_data = data.get("inventory", {})
                merchant.set_inventory(inventory_data)
                
                # Set restock
                merchant.daily_restock = data.get("daily_restock", {})
                
                self.merchants[merchant_id] = merchant
                
        except FileNotFoundError:
            print(f"Merchants file not found at {file_path}")
            self._create_default_merchants()
        except Exception as e:
            print(f"Error loading merchants: {e}")
            self._create_default_merchants()
            
    def _create_default_merchants(self):
        """Create basic default merchants."""
        # Downtown general store
        downtown_store = Merchant(
            merchant_id="downtown_general",
            name="Downtown Convenience",
            location="Downtown",
            merchant_type="regular"
        )
        downtown_store.specialty_categories = ["food", "drink", "misc"]
        downtown_store.base_markup = 1.3  # Higher prices downtown
        downtown_store.set_inventory({
            "food_sandwich": 10,
            "food_canned_beans": 20,
            "drink_water_bottle": 30,
            "clothing_socks": 5
        })
        downtown_store.daily_restock = {
            "food_sandwich": 10,
            "food_canned_beans": 5,
            "drink_water_bottle": 15,
            "clothing_socks": 2
        }
        self.merchants["downtown_general"] = downtown_store
        
        # Outreach center (subsidized goods)
        outreach = Merchant(
            merchant_id="shelter_outreach",
            name="Community Outreach Center",
            location="Vanier",
            merchant_type="regular",
            faction="shelter_network"
        )
        outreach.specialty_categories = ["food", "clothing", "hygiene"]
        outreach.base_markup = 0.8  # Lower prices due to subsidies
        outreach.haggle_difficulty = 90  # Very hard to haggle (fixed prices)
        outreach.set_inventory({
            "food_sandwich": 5,
            "food_canned_beans": 15,
            "clothing_socks": 10,
            "sleeping_bag": 2
        })
        outreach.daily_restock = {
            "food_sandwich": 5,
            "food_canned_beans": 5,
            "clothing_socks": 3,
            "sleeping_bag": 1
        }
        self.merchants["shelter_outreach"] = outreach
        
        # Black market dealer
        black_market = Merchant(
            merchant_id="street_dealer",
            name="Street Dealer",
            location="ByWard Market",
            merchant_type="black_market",
            faction="street_crew"
        )
        black_market.specialty_categories = ["medical", "stolen"]
        black_market.base_markup = 2.0  # Much higher prices for illegal goods
        black_market.haggle_difficulty = 40  # Easier to haggle
        black_market.set_inventory({
            "narcotic_painkillers": 5
        })
        black_market.daily_restock = {
            "narcotic_painkillers": 2
        }
        self.merchants["street_dealer"] = black_market
    
    def _initialize_economy(self):
        """Set up initial economic conditions."""
        # Set location modifiers
        self.location_modifiers = {
            "Downtown": 1.2,  # Higher prices
            "ByWard Market": 1.0,  # Standard prices
            "Vanier": 0.8,  # Lower prices
            "Glebe": 1.3,  # Premium prices
            "Centretown": 1.1,  # Slightly higher
            "Overbrook": 0.9,  # Slightly lower
            "Hintonburg": 1.1
        }
        
        # Set initial category demand
        categories = {item.category for item in self.items.values()}
        self.category_demand = {
            category: random.uniform(0.8, 1.2) for category in categories
        }
        
        # Add some initial economic events
        self._create_random_economic_event()
        
    def update(self, day: int, season: str = None):
        """Update economy state for a new day.
        
        Args:
            day: Current game day
            season: Current season (optional)
        """
        self.current_day = day
        if season:
            self.current_season = season
            
        # Update economic events
        for event in self.economic_events:
            event.update()
        # Remove expired events
        self.economic_events = [e for e in self.economic_events if e.active]
        
        # Restock merchants
        for merchant in self.merchants.values():
            merchant.restock(day, self)
            
        # Update category demand (gradual shifts)
        for category in self.category_demand:
            # Chance for demand to shift 
            if random.random() < 0.2:  # 20% chance per day
                # Current demand
                current = self.category_demand[category]
                # Target (random walk)
                shift = random.uniform(-0.1, 0.1)
                # New demand with limits
                self.category_demand[category] = max(0.5, min(1.5, current + shift))
                
        # Update global economy (rare shifts)
        if random.random() < 0.05:  # 5% chance per day
            shift = random.uniform(-0.05, 0.05)
            self.global_economy = max(0.8, min(1.2, self.global_economy + shift))
            
        # Create new economic events occasionally
        if random.random() < 0.1:  # 10% chance per day
            self._create_random_economic_event()
    
    def get_merchant(self, merchant_id: str) -> Optional[Merchant]:
        """Get a merchant by ID.
        
        Args:
            merchant_id: Merchant ID
            
        Returns:
            Merchant or None
        """
        return self.merchants.get(merchant_id)
    
    def get_item(self, item_id: str) -> Optional[Item]:
        """Get an item by ID.
        
        Args:
            item_id: Item ID
            
        Returns:
            Item or None
        """
        return self.items.get(item_id)
    
    def get_merchants_in_location(self, location: str) -> List[Merchant]:
        """Get all merchants in a specific location.
        
        Args:
            location: Location name
            
        Returns:
            list: Merchants in the location
        """
        return [m for m in self.merchants.values() if m.location == location]
    
    def get_location_modifier(self, location: str) -> float:
        """Get economic modifier for a location.
        
        Args:
            location: Location name
            
        Returns:
            float: Location economic modifier
        """
        return self.location_modifiers.get(location, 1.0)
    
    def get_global_modifier(self) -> float:
        """Get global economic modifier.
        
        Returns:
            float: Global economic modifier
        """
        return self.global_economy
    
    def get_category_demand(self, category: str) -> float:
        """Get demand modifier for an item category.
        
        Args:
            category: Item category
            
        Returns:
            float: Demand modifier
        """
        return self.category_demand.get(category, 1.0)
    
    def get_all_items(self) -> Dict[str, Item]:
        """Get all items in the economy.
        
        Returns:
            dict: All items
        """
        return self.items.copy()
    
    def get_event_modifier(self, item_id: str, category: str) -> float:
        """Get combined event modifier for an item.
        
        Args:
            item_id: Item ID
            category: Item category
            
        Returns:
            float: Combined event modifier
        """
        if not self.economic_events:
            return 1.0
            
        # Combine modifiers from all active events affecting this item
        modifier = 1.0
        for event in self.economic_events:
            if event.active and event.affects_item(item_id, category):
                modifier *= event.get_price_modifier(item_id, category)
                
        return modifier
    
    def get_item_price_history(self, item_id: str) -> List[float]:
        """Get price history for an item.
        
        Args:
            item_id: Item ID
            
        Returns:
            list: Price history
        """
        if item_id not in self.price_histories:
            self.price_histories[item_id] = []
        return self.price_histories[item_id].copy()
    
    def record_price(self, item_id: str, price: float):
        """Record a price in the price history.
        
        Args:
            item_id: Item ID
            price: Price paid
        """
        if item_id not in self.price_histories:
            self.price_histories[item_id] = []
            
        history = self.price_histories[item_id]
        history.append(price)
        
        # Keep only recent history
        if len(history) > 20:
            history.pop(0)
    
    def _create_random_economic_event(self):
        """Create a random economic event."""
        # Event types
        event_types = [
            "price_surge",
            "price_crash",
            "supply_shortage",
            "supply_glut",
            "seasonal_demand",
            "quality_issue"
        ]
        
        # Pick random type and category
        event_type = random.choice(event_types)
        categories = list(self.category_demand.keys())
        
        if not categories:
            return  # No categories to affect
            
        affected_category = random.choice(categories)
        
        # Create appropriate event
        if event_type == "price_surge":
            duration = random.randint(3, 7)  # 3-7 days
            event = EconomicEvent(
                event_id=f"surge_{affected_category}_{self.current_day}",
                name=f"{affected_category.title()} Price Surge",
                description=f"Prices for {affected_category} items have increased substantially.",
                duration=duration
            )
            event.affected_categories = [affected_category]
            event.price_modifiers = {affected_category: random.uniform(1.3, 1.8)}
            event.news_headline = f"Rising {affected_category} prices affect local markets"
            
        elif event_type == "price_crash":
            duration = random.randint(2, 5)  # 2-5 days
            event = EconomicEvent(
                event_id=f"crash_{affected_category}_{self.current_day}",
                name=f"{affected_category.title()} Price Crash",
                description=f"Prices for {affected_category} items have dropped significantly.",
                duration=duration
            )
            event.affected_categories = [affected_category]
            event.price_modifiers = {affected_category: random.uniform(0.5, 0.8)}
            event.news_headline = f"{affected_category.title()} market crashes, bargains available"
            
        elif event_type == "supply_shortage":
            duration = random.randint(4, 8)  # 4-8 days
            event = EconomicEvent(
                event_id=f"shortage_{affected_category}_{self.current_day}",
                name=f"{affected_category.title()} Shortage",
                description=f"Supply of {affected_category} items is limited.",
                duration=duration
            )
            event.affected_categories = [affected_category]
            event.price_modifiers = {affected_category: random.uniform(1.2, 1.5)}
            event.availability_modifiers = {affected_category: random.uniform(0.3, 0.7)}
            event.news_headline = f"Supply chain issues cause {affected_category} shortages"
            
        elif event_type == "supply_glut":
            duration = random.randint(3, 6)  # 3-6 days
            event = EconomicEvent(
                event_id=f"glut_{affected_category}_{self.current_day}",
                name=f"{affected_category.title()} Surplus",
                description=f"Oversupply of {affected_category} items has reduced prices.",
                duration=duration
            )
            event.affected_categories = [affected_category]
            event.price_modifiers = {affected_category: random.uniform(0.6, 0.9)}
            event.availability_modifiers = {affected_category: random.uniform(1.3, 1.8)}
            event.news_headline = f"Excess {affected_category} supply leads to bargains"
            
        elif event_type == "seasonal_demand":
            duration = random.randint(5, 10)  # 5-10 days
            season_effects = {
                "winter": ["clothing", "survival", "food"],
                "spring": ["tool", "medicinal", "hygiene"],
                "summer": ["drink", "leisure", "hygiene"],
                "fall": ["clothing", "food", "tool"]
            }
            # Find categories relevant to current season
            relevant = season_effects.get(self.current_season, [])
            if relevant and affected_category in relevant:
                event = EconomicEvent(
                    event_id=f"seasonal_{affected_category}_{self.current_day}",
                    name=f"Seasonal {affected_category.title()} Demand",
                    description=f"Seasonal demand has affected {affected_category} prices.",
                    duration=duration
                )
                event.affected_categories = [affected_category]
                event.price_modifiers = {affected_category: random.uniform(1.1, 1.4)}
                event.news_headline = f"Seasonal needs drive {affected_category} demand"
            else:
                # Not a seasonal category, create a different event
                return self._create_random_economic_event()
                
        elif event_type == "quality_issue":
            duration = random.randint(2, 4)  # 2-4 days
            event = EconomicEvent(
                event_id=f"quality_{affected_category}_{self.current_day}",
                name=f"{affected_category.title()} Quality Issues",
                description=f"Quality concerns have affected {affected_category} items.",
                duration=duration
            )
            event.affected_categories = [affected_category]
            event.price_modifiers = {affected_category: random.uniform(0.7, 0.9)}
            event.news_headline = f"Quality concerns impact {affected_category} market"
            
        else:
            # Fallback - simple price fluctuation
            duration = random.randint(2, 5)
            event = EconomicEvent(
                event_id=f"fluctuation_{affected_category}_{self.current_day}",
                name=f"{affected_category.title()} Market Fluctuation",
                description=f"Normal market fluctuations in {affected_category} prices.",
                duration=duration
            )
            event.affected_categories = [affected_category]
            event.price_modifiers = {affected_category: random.uniform(0.85, 1.15)}
            
        # Add event to active events
        self.economic_events.append(event)
        
    def get_news_headlines(self) -> List[str]:
        """Get current economic news headlines.
        
        Returns:
            list: News headlines
        """
        headlines = []
        
        # Get headlines from active events
        for event in self.economic_events:
            if event.active:
                news = event.get_news()
                if news:
                    headlines.append(news)
                    
        # Add general economic news
        if self.global_economy > 1.1:
            headlines.append("Local economy showing signs of growth.")
        elif self.global_economy < 0.9:
            headlines.append("Economic downturn affecting local businesses.")
            
        # Add news about extreme category demand
        for category, demand in self.category_demand.items():
            if demand > 1.3:
                headlines.append(f"High demand for {category} items reported.")
            elif demand < 0.7:
                headlines.append(f"Falling demand for {category} items noted.")
                
        return headlines
    
    def get_economic_status(self) -> Dict:
        """Get current economic status summary.
        
        Returns:
            dict: Economic status summary
        """
        return {
            "global_economy": self.global_economy,
            "season": self.current_season,
            "active_events": len(self.economic_events),
            "categories": self.category_demand.copy(),
            "black_market_status": "active" if any(m.type == "black_market" for m in self.merchants.values()) else "unknown"
        }
    
    def serialize(self) -> Dict:
        """Serialize economy data for saving."""
        # Basic economy data
        data = {
            "global_economy": self.global_economy,
            "current_day": self.current_day,
            "current_season": self.current_season,
            "category_demand": self.category_demand,
            "location_modifiers": self.location_modifiers,
            # More detailed data below
            "merchants": {},
            "active_events": []
        }
        
        # Serialize merchant data
        for merchant_id, merchant in self.merchants.items():
            data["merchants"][merchant_id] = {
                "inventory": merchant.inventory,
                "price_modifiers": merchant.price_modifiers,
                "special_offers": merchant.special_offers,
                "last_restock_day": merchant.last_restock_day
            }
            
        # Serialize active events
        for event in self.economic_events:
            if event.active:
                data["active_events"].append({
                    "id": event.id,
                    "name": event.name,
                    "description": event.description,
                    "duration": event.duration,
                    "remaining_duration": event.remaining_duration,
                    "affected_categories": event.affected_categories,
                    "affected_items": event.affected_items,
                    "price_modifiers": event.price_modifiers,
                    "availability_modifiers": event.availability_modifiers,
                    "location_specific": event.location_specific,
                    "news_headline": event.news_headline
                })
                
        return data