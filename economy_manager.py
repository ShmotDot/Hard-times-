
"""
Economy manager for coordinating economic systems.
"""
from game.economy import Shop, BlackMarket, JobSystem
import random
import time

class EconomyManager:
    def __init__(self):
        self.shops = {}
        self.black_market = BlackMarket()
        self.job_system = JobSystem()
        self.global_economy = 0.5  # Economic health (0-1)
        self.local_demand = {}  # Demand by location
        self.price_history = {}  # Track price changes
        self.trade_cooldowns = {}  # Prevent trade spam
        
    def initialize_economy(self):
        """Set up initial economic state."""
        self.market_events = []
        self.economic_stability = 1.0  # 0.0-2.0, 1.0 is stable
        
        # Initialize shops with location-specific pricing
        base_prices = {
            # Essential items
            "food_sandwich": 5.00,
            "drink_water_bottle": 2.00,
            "medicine_bandage": 3.50,
            "food_apple": 1.00,
            "food_canned_beans": 2.50,
            "clothing_socks": 5.00,
            "tool_lighter": 3.00,
            # Luxury items
            "coffee": 3.50,
            "snack_chips": 2.50,
            "chocolate_bar": 2.00,
            # Survival items  
            "sleeping_bag": 25.00,
            "tarp": 15.00,
            "backpack": 30.00
        }
        
        # Track item categories for economic events
        self.item_categories = {
            "essential": ["food_sandwich", "drink_water_bottle", "medicine_bandage"],
            "luxury": ["coffee", "snack_chips", "chocolate_bar"],
            "survival": ["sleeping_bag", "tarp", "backpack"]
        }
        
        location_modifiers = {
            "Downtown": 1.2,  # Higher prices
            "ByWard Market": 1.0,  # Standard prices
            "Vanier": 0.8,  # Lower prices
            "Glebe": 1.3,  # Premium prices
            "Centretown": 1.1
        }
        
        for location, modifier in location_modifiers.items():
            adjusted_prices = {item: price * modifier 
                             for item, price in base_prices.items()}
            
            self.shops[f"{location.lower()}_market"] = Shop(
                f"{location} Market",
                location,
                adjusted_prices
            )
            self.local_demand[location] = random.uniform(0.3, 0.8)
            
    def update_economy(self, time_system, weather_system=None):
        """Update economic conditions based on time, weather, and events."""
        # Process economic events
        self._process_economic_events()
        
        # Weather effects
        season_modifier = 0.0
        if weather_system:
            if weather_system.current_weather in ["snow", "storm"]:
                season_modifier -= 0.1
                self._trigger_weather_event("winter_prices")
            elif weather_system.current_weather == "heatwave":
                season_modifier += 0.15
                self._trigger_weather_event("summer_prices")
            elif weather_system.current_weather in ["clear", "sunny"]:
                season_modifier += 0.05
                
    def _process_economic_events(self):
        """Process active economic events."""
        for event in self.market_events:
            if event["type"] == "price_shock":
                self._apply_price_shock(event)
            elif event["type"] == "supply_shortage":
                self._apply_supply_shortage(event)
            elif event["type"] == "market_boom":
                self._apply_market_boom(event)
                
        # Clean up expired events
        self.market_events = [e for e in self.market_events if e["duration"] > 0]
        
    def _trigger_weather_event(self, event_type):
        """Trigger weather-related economic events."""
        if event_type == "winter_prices":
            # Increase prices of winter survival items
            self.market_events.append({
                "type": "price_shock",
                "category": "survival",
                "modifier": 1.5,
                "duration": 24,  # Hours
                "description": "Winter weather has increased demand for survival gear."
            })
        elif event_type == "summer_prices":
            # Increase prices of water and cooling items
            self.market_events.append({
                "type": "price_shock",
                "items": ["drink_water_bottle"],
                "modifier": 1.3,
                "duration": 12,
                "description": "Heatwave has increased water prices."
            })
            
    def _apply_price_shock(self, event):
        """Apply a price shock to affected items."""
        if "category" in event:
            items = self.item_categories.get(event["category"], [])
        else:
            items = event.get("items", [])
            
        for shop in self.shops.values():
            for item_id in items:
                if item_id in shop.current_prices:
                    shop.current_prices[item_id] *= event["modifier"]
                    
        event["duration"] -= 1
        
        # Time of day effects        
        time_modifier = 0.0
        current_period = time_system.get_period()
        if current_period in ["morning", "afternoon"]:
            time_modifier += 0.03
        elif current_period == "night":
            time_modifier -= 0.05
        
        # Update global economy
        self.global_economy += random.uniform(-0.05, 0.05) + season_modifier + time_modifier
        self.global_economy = max(0.1, min(1.0, self.global_economy))
        
        # Generate new jobs based on economic conditions
        if random.random() < self.global_economy:
            self._generate_new_jobs()
            
        # Update local demand with neighboring effects
        self._update_local_demand()
        
        # Update shop prices
        self._update_shop_prices(time_system)
        
    def _update_local_demand(self):
        """Update local demand with neighboring location influences."""
        location_connections = {
            "Downtown": ["ByWard Market", "Centretown"],
            "ByWard Market": ["Downtown", "Lowertown"],
            "Centretown": ["Downtown", "Glebe"],
            "Glebe": ["Centretown", "Old Ottawa South"],
            "Vanier": ["Lowertown", "Overbrook"]
        }
        
        new_demand = self.local_demand.copy()
        for location, neighbors in location_connections.items():
            neighbor_avg = sum(self.local_demand.get(n, 0.5) for n in neighbors) / len(neighbors)
            new_demand[location] = (new_demand[location] * 0.7 + neighbor_avg * 0.3 + 
                                  random.uniform(-0.1, 0.1))
            new_demand[location] = max(0.1, min(1.0, new_demand[location]))
            
        self.local_demand = new_demand
        
    def _update_shop_prices(self, time_system):
        """Update shop prices based on various factors."""
        current_hour = time_system.get_hour()
        
        for shop in self.shops.values():
            location_demand = self.local_demand.get(shop.location, 0.5)
            
            # Calculate dynamic price modifiers
            time_modifier = 1.0
            if current_hour < 8:  # Early morning discount
                time_modifier = 0.9
            elif current_hour > 20:  # Late night premium
                time_modifier = 1.1
                
            # Update each item's price
            for item_id in shop.base_prices:
                base_price = shop.base_prices[item_id]
                
                # Calculate new price with all modifiers
                new_price = base_price * (
                    time_modifier *
                    (0.8 + location_demand * 0.4) *  # Local demand impact
                    (0.9 + self.global_economy * 0.2)  # Global economy impact
                )
                
                # Add some random fluctuation
                new_price *= random.uniform(0.95, 1.05)
                
                # Round to 2 decimal places
                shop.current_prices[item_id] = round(new_price, 2)
                
                # Track price history
                if item_id not in self.price_history:
                    self.price_history[item_id] = []
                self.price_history[item_id].append(new_price)
                if len(self.price_history[item_id]) > 24:  # Keep last 24 hours
                    self.price_history[item_id].pop(0)
                    
    def get_best_price(self, item_id):
        """Find the best price for an item across all shops."""
        best_price = float('inf')
        best_shop = None
        avg_price = 0
        total_shops = 0
        
        for shop in self.shops.values():
            if item_id in shop.current_prices:
                price = shop.current_prices[item_id]
                avg_price += price
                total_shops += 1
                if price < best_price:
                    best_price = price
                    best_shop = shop
        
        if total_shops > 0:
            avg_price /= total_shops
            # Return shop, price, and whether it's a good deal (>10% below average)
            is_good_deal = best_price < (avg_price * 0.9)
            return best_shop, best_price, is_good_deal
            
        return None, None, False
        
    def get_daily_deals(self):
        """Get the best deals across all shops."""
        deals = []
        for category, items in self.item_categories.items():
            for item_id in items:
                shop, price, is_good_deal = self.get_best_price(item_id)
                if shop and is_good_deal:
                    deals.append({
                        "item_id": item_id,
                        "shop": shop.name,
                        "price": price,
                        "category": category
                    })
        return deals
        
    def can_trade(self, player_id, npc_id):
        """Check if trading is allowed (prevent spam)."""
        trade_key = f"{player_id}_{npc_id}"
        last_trade = self.trade_cooldowns.get(trade_key, 0)
        current_time = time.time()
        
        if current_time - last_trade < 300:  # 5 minute cooldown
            return False
        return True
        
    def record_trade(self, player_id, npc_id):
        """Record a trade interaction."""
        trade_key = f"{player_id}_{npc_id}"
        self.trade_cooldowns[trade_key] = time.time()
