
"""
Enhanced Tutorial system for Hard Times: Ottawa
Provides interactive learning, contextual help, and progressive guidance
"""

from game.utils import safe_input
import time
import random
import sys
from datetime import datetime

class Tutorial:
    def __init__(self, ui, player, resource_manager=None, location_manager=None, time_system=None):
        self.ui = ui
        self.player = player
        self.resource_manager = resource_manager
        self.location_manager = location_manager
        self.time_system = time_system
        self.completed = False
        self.quick_tutorial = False
        self.tips_shown = set()  # Track which tips have been shown
        self.tutorial_progress = 0  # Track overall tutorial completion percentage
        self.last_help_timestamp = 0  # Track when help was last shown to avoid spam
        
        # Dictionary of gameplay tips for various situations
        self.gameplay_tips = {
            # Critical stat warnings
            "low_health": "⚠️ WARNING: Your health is critically low! Find medical attention or rest immediately.",
            "low_satiety": "⚠️ WARNING: You're starving! Find food as soon as possible to avoid health damage.",
            "low_energy": "⚠️ WARNING: You're exhausted! Rest soon or your health will start to suffer.",
            "low_mental": "⚠️ WARNING: Your mental state is deteriorating. Find a safe place to rest and recover.",
            "low_hygiene": "⚠️ WARNING: Your hygiene is very poor. Find a place to clean up to avoid infection.",
            
            # Weather warnings
            "cold_weather": "⚠️ WEATHER ALERT: It's dangerously cold! Find warm shelter or you'll lose health quickly.",
            "rain_warning": "⚠️ WEATHER ALERT: It's raining. Find shelter or your health and hygiene will suffer.",
            
            # First-time action tips
            "first_explore": "TIP: Exploring can reveal opportunities, resources, and events. Each exploration takes 1 hour of game time.",
            "first_scavenge": "TIP: Scavenging can yield useful items, but success varies by location and time of day.",
            "first_rest": "TIP: Resting recovers energy but the quality depends on your location, time of day, and weather.",
            
            # Feature unlock tips
            "feature_unlock_crafting": "NEW FEATURE: Crafting is now available! You can create useful items from materials you've collected.",
            "feature_unlock_shops": "NEW FEATURE: Shops are now available! You can purchase items if you have money.",
            "feature_unlock_work": "NEW FEATURE: Work opportunities are now available! Check specific locations for jobs.",
            
            # General tips
            "shelter_time": "TIP: Most shelters only accept new people in the evening, typically between 5PM and 9PM.",
            "food_bank_time": "TIP: Food banks usually operate during daytime hours, often from 9AM to 3PM.",
            "resource_management": "TIP: Plan your day around the resources you need most - food, shelter, or money."
        }
        
        # Startup flags for tutorial completion tracking (enhanced with progress weights)
        self.sections_completed = {
            "intro": {"completed": False, "weight": 5},
            "stats": {"completed": False, "weight": 15},
            "inventory": {"completed": False, "weight": 15},
            "locations": {"completed": False, "weight": 15},
            "services": {"completed": False, "weight": 15},
            "features": {"completed": False, "weight": 15},
            "activities": {"completed": False, "weight": 20}
        }
        
        # Core tutorial steps
        self.steps = [
            {
                "title": "Welcome to Hard Times: Ottawa",
                "text": "You are about to experience life on the streets of Ottawa. This enhanced tutorial will help you understand survival mechanics through interactive demonstrations and practice.",
                "action": "Press Enter to begin your journey...",
                "section": "intro"
            },
            {
                "title": "Your Character: Devin",
                "text": "You play as Devin, recently homeless due to mental health struggles and job loss. Your immediate goals are survival and finding stability.",
                "action": "Press Enter to learn about your vital stats...",
                "section": "intro"
            },
            {
                "title": "Vital Statistics",
                "text": """You must manage several vital stats:
• Health (♥): Your physical condition
• Satiety (🍽): How satisfied/full you are (higher is better)
• Energy (⚡): Your stamina level
• Mental (🧠): Your psychological well-being
• Hygiene (🚿): Your cleanliness level""",
                "action": "Press Enter to see your current stats...",
                "section": "stats",
                "interaction": "show_stats"
            },
            {
                "title": "Stat Effects and Warnings",
                "text": """Your stats affect gameplay in realistic ways:
• Low Health: Risk of death (game over)
• Low Satiety: Energy drain, health damage
• Low Energy: Limited actions, slower movement
• Low Mental: Affects decision-making, risk of breakdown
• Low Hygiene: Increased infection risk, social rejection

When stats reach critical levels, you'll receive warnings.""",
                "action": "Press Enter to learn about time and weather...",
                "section": "stats"
            },
            {
                "title": "Time and Weather",
                "text": """The game follows a realistic time system:
• Activities take time
• Services have operating hours
• Weather changes affect survival
• Temperature impacts health

Cold and wet conditions are especially dangerous when homeless.""",
                "action": "Press Enter to learn about inventory...",
                "section": "stats"
            },
            {
                "title": "Inventory Management",
                "text": """Your inventory represents items you carry:
• Limited by weight capacity
• Items have quality and condition
• Food can expire
• Clothing affects temperature resistance
• Items can be used, traded, or crafted""",
                "action": "Press Enter to see your starting inventory...",
                "section": "inventory",
                "interaction": "show_inventory"
            },
            {
                "title": "Finding and Using Items",
                "text": """Items can be acquired through:
• Scavenging in locations
• Purchasing from shops
• Receiving from services
• Trading with others
• Crafting from components

Use items to manage your stats and survive.""",
                "action": "Press Enter to try using an item...",
                "section": "inventory",
                "interaction": "demo_use_item"
            },
            {
                "title": "Basic Survival",
                "text": """To survive, you'll need to:
1. Find food through meal programs, food banks, or scavenging
2. Find safe places to sleep (shelters or hidden spots)
3. Maintain hygiene to avoid health issues
4. Manage your mental health
5. Stay warm and dry""",
                "action": "Press Enter to learn about locations...",
                "section": "inventory"
            },
            {
                "title": "Locations & Travel",
                "text": """Different areas offer different resources:
• Downtown: More opportunities but higher risk
• Shelters: Safe sleep but limited space
• Food Banks: Regular meals but limited hours
• Parks: Places to rest but exposed to weather
• Libraries: Warm and safe during operating hours""",
                "action": "Press Enter to try traveling...",
                "section": "locations",
                "interaction": "demo_travel"
            },
            {
                "title": "Discovering the Map",
                "text": """As you explore Ottawa, you'll discover new locations:
• The map tracks where you've been
• Travel takes time and energy
• Some areas are only accessible from certain locations
• Weather affects travel time and safety

You can always view discovered locations from the map option.""",
                "action": "Press Enter for social services info...",
                "section": "locations"
            },
            {
                "title": "Social Services",
                "text": """Available services include:
• Emergency shelters
• Food banks
• Medical clinics
• Mental health services
• Housing assistance
• Employment programs

Services have specific locations and operating hours.""",
                "action": "Press Enter to learn about accessing services...",
                "section": "services"
            },
            {
                "title": "Accessing Services",
                "text": """To use services effectively:
• Visit the correct location during operating hours
• Some services have limited availability
• Building relationships improves service access
• ID and documentation help with applications
• Services can significantly improve your situation""",
                "action": "Press Enter to try accessing a service...",
                "section": "services",
                "interaction": "demo_services"
            },
            {
                "title": "Feature Availability System",
                "text": """As you progress, new features will unlock:
• Crafting: Unlocks when you find specific materials
• Shops: Open after a few days of survival
• Work: Requires clean clothes and proper location
• Black Market: Requires street reputation or connections

This creates a realistic progression system.""",
                "action": "Press Enter to see current unlocked features...",
                "section": "features",
                "interaction": "show_unlocked_features"
            },
            {
                "title": "Skills & Reputation",
                "text": """You can develop various skills:
• Foraging: Finding food and resources
• Bartering: Getting better deals
• Street Smarts: Avoiding danger
• Social: Interacting with others
• Survival: Resisting environmental effects

Skills improve through related activities.""",
                "action": "Press Enter to see your starting skills...",
                "section": "features",
                "interaction": "show_skills"
            },
            {
                "title": "Relationships & Reputation",
                "text": """Your reputation affects how others treat you:
• Police: Affects law enforcement interactions
• Shelters: Affects access to beds and resources
• Community: Affects general assistance
• Street: Affects information and opportunities
• Services: Affects application success rates

Building relationships takes time but offers huge benefits.""",
                "action": "Press Enter to learn about activities...",
                "section": "features"
            },
            {
                "title": "Daily Activities",
                "text": """A typical day might include:
• Morning: Find food, check services, apply for assistance
• Afternoon: Scavenge, look for work, improve skills
• Evening: Find shelter, prepare for night
• Night: Rest, stay safe

Planning your day efficiently is crucial for survival.""",
                "action": "Press Enter to try a scavenging activity...",
                "section": "activities",
                "interaction": "demo_scavenging"
            },
            {
                "title": "Events & Encounters",
                "text": """You'll experience random events:
• Weather changes
• NPC encounters
• Service opportunities
• Dangerous situations
• Story developments

Your choices during events shape your journey.""",
                "action": "Press Enter to experience a sample event...",
                "section": "activities",
                "interaction": "demo_event"
            },
            {
                "title": "Progress & Victory",
                "text": """To win the game, you need to:
• Build housing prospects (find stable housing)
• Develop job prospects (find employment)
• Maintain mental health
• Stay out of trouble with law enforcement

This won't be easy, but there are people and resources to help.""",
                "action": "Press Enter for final tips...",
                "section": "activities"
            },
            {
                "title": "Tutorial Help System",
                "text": """During gameplay, you'll receive contextual tips:
• First-time action tips
• Critical stat warnings
• Feature unlock notifications
• Seasonal advice
• Location-specific guidance

These tips will help you learn as you play.""",
                "action": "Press Enter to complete the tutorial...",
                "section": "activities"
            }
        ]
        
        # The gameplay_tips dictionary is already defined above

    def run(self):
        """Run the enhanced tutorial sequence."""
        self.ui.clear_screen()
        
        # Ask if player wants full tutorial or quick start
        self.ui.display_title("Tutorial Options")
        self.ui.display_text("How would you like to learn the game?")
        self.ui.display_text("1. Full Tutorial (Recommended for new players)")
        self.ui.display_text("2. Quick Start Guide (Basic info only)")
        self.ui.display_text("3. Skip Tutorial (For experienced players)")
        
        while True:
            choice = safe_input("\nEnter your choice (1-3): ")
            
            # Handle timeout or invalid input by using default option (Quick Start)
            if choice is None:
                choice = "2"  # Default to Quick Start if timeout
                self.ui.display_text("Defaulting to Quick Start Guide...")
                time.sleep(1)
                
            if choice == "1":
                self._run_full_tutorial()
                break
            elif choice == "2":
                self._run_quick_tutorial()
                break
            elif choice == "3":
                self.completed = True
                self.ui.display_success("Tutorial skipped. Good luck on the streets!")
                safe_input("Press Enter to start the game...")
                break
            else:
                self.ui.display_error("Invalid choice. Please enter 1, 2, or 3.")
        
    def _run_full_tutorial(self):
        """Run the comprehensive tutorial with all steps."""
        step_count = len(self.steps)
        for i, step in enumerate(self.steps, 1):
            self.ui.clear_screen()
            
            # Display progress
            progress_percent = (i / step_count) * 100
            self.tutorial_progress = progress_percent
            progress_bar = self._generate_progress_bar(progress_percent)
            self.ui.display_text(f"Tutorial Progress: {progress_bar} {int(progress_percent)}%", "cyan")
            
            # Display tutorial content
            self.ui.display_title(step["title"])
            self.ui.display_text(step["text"])
            self.ui.display_divider()
            
            # Mark section as completed
            if "section" in step and step["section"] in self.sections_completed:
                section_dict = self.sections_completed[step["section"]]
                section_dict["completed"] = True
                self.sections_completed[step["section"]] = section_dict
                self._update_progress()
            
            # Add small delay for readability
            time.sleep(0.5)
            
            # Interactive element based on step
            if "interaction" in step:
                self.handle_interaction(step["interaction"])
            
            # Show useful keyboard shortcuts at bottom
            self.ui.display_text("", "reset")  # Add some space
            self.ui.display_text("TIP: During the real game, press 'h' at any time for help", "yellow")
            safe_input(step["action"])
            
        self.completed = True
        self.ui.clear_screen()
        
        # Show completion certificate
        self._display_completion_certificate()
        
        self.ui.display_success("Tutorial completed! You're now ready to begin your journey.")
        self.ui.display_text("\nRemember, survival is just the first step. Your ultimate goal is to find stability.")
        self.ui.display_text("You'll continue to receive helpful tips as you encounter new situations.")
        
        # Display recap of key concepts
        self.ui.display_subtitle("Key Concepts Recap:")
        self.ui.display_text("• Monitor and maintain your vital stats")
        self.ui.display_text("• Find food and shelter daily")
        self.ui.display_text("• Explore to discover opportunities")
        self.ui.display_text("• Use services during their operating hours")
        self.ui.display_text("• Develop skills and reputation")
        self.ui.display_text("• Press 'h' anytime for help")
        
        safe_input("Press Enter to start the game...")
    
    def _run_quick_tutorial(self):
        """Run a condensed version of the tutorial with only essential information."""
        quick_steps = [
            {
                "title": "Welcome to Hard Times: Ottawa",
                "text": "This quick guide will cover just the essentials. You'll receive tips during gameplay to help you learn.",
                "action": "Press Enter to continue..."
            },
            {
                "title": "Core Survival Mechanics",
                "text": """QUICK GUIDE:
• Manage health, satiety, energy, mental state, and hygiene
• Find food and shelter daily to survive
• Weather affects survival (cold, rain are dangerous)
• Travel between locations to find resources
• Develop skills and reputation
• Work toward housing and employment stability""",
                "action": "Press Enter to see your stats...",
                "interaction": "show_stats"
            },
            {
                "title": "Game Features",
                "text": """AVAILABLE ACTIVITIES:
• Explore locations for events and opportunities
• Scavenge for useful items
• Rest to recover energy
• Use services (shelters, food banks, clinics)
• Look for work opportunities
• Build relationships with NPCs

New features will unlock as you progress.""",
                "action": "Press Enter to see your inventory...",
                "interaction": "show_inventory"
            },
            {
                "title": "Learning As You Go",
                "text": """The game includes an in-game help system that will:
• Provide contextual tips for new situations
• Warn about dangerous conditions
• Explain newly unlocked features
• Offer situation-specific advice

Remember to watch your stats and plan each day carefully.""",
                "action": "Press Enter to continue..."
            },
            {
                "title": "Interactive Help System",
                "text": """You can access help at any time by pressing 'h' during gameplay.
The help system provides:
• Basic controls and commands
• Survival tips based on your current situation
• Goal reminders to keep you on track
• Strategy recommendations

Try it out during the game if you get stuck!""",
                "action": "Press Enter to try the help system...",
                "interaction": "demo_help"
            }
        ]
        
        step_count = len(quick_steps)
        for i, step in enumerate(quick_steps, 1):
            self.ui.clear_screen()
            
            # Display progress
            progress_percent = (i / step_count) * 100
            progress_bar = self._generate_progress_bar(progress_percent)
            self.ui.display_text(f"Quick Guide Progress: {progress_bar} {int(progress_percent)}%", "cyan")
            
            # Display tutorial content
            self.ui.display_title(step["title"])
            self.ui.display_text(step["text"])
            self.ui.display_divider()
            
            # Add small delay for readability
            time.sleep(0.5)
            
            # Interactive element based on step
            if "interaction" in step:
                self.handle_interaction(step["interaction"])
            
            # Show tip about help system
            self.ui.display_text("\nTIP: Press 'h' at any time during gameplay for help", "yellow")
            safe_input(step["action"])
        
        # Mark as completed but note it was the quick version
        self.completed = True
        self.quick_tutorial = True
        
        self.ui.clear_screen()
        self.ui.display_success("Quick guide completed! You're now ready to begin.")
        self.ui.display_text("\nYou'll receive additional tips during gameplay to help you learn.")
        
        # Display key reminders
        self.ui.display_subtitle("Key Reminders:")
        self.ui.display_text("• Monitor your stats (health, satiety, energy, mental, hygiene)")
        self.ui.display_text("• Find food and shelter daily to survive")
        self.ui.display_text("• Press 'h' anytime to access the help system")
        
        safe_input("Press Enter to start the game...")
        
    def handle_interaction(self, interaction):
        """Handle interactive tutorial elements."""
        if interaction == "show_stats":
            self.ui.display_subtitle("Your Current Stats")
            self.ui.display_text(f"Health: {self.player.health}/100")
            self.ui.display_text(f"Satiety: {self.player.satiety}/100 (higher is better)")
            self.ui.display_text(f"Energy: {self.player.energy}/100")
            self.ui.display_text(f"Mental: {self.player.mental}/100")
            self.ui.display_text(f"Hygiene: {self.player.hygiene}/100")
            self.ui.display_text("\nMoney: ${:.2f}".format(self.player.money))
            
        elif interaction == "show_inventory":
            self.ui.display_subtitle("Your Starting Items")
            if not self.player.inventory.items:
                self.ui.display_text("You have no items yet.")
            else:
                for item_id, item in self.player.inventory.items.items():
                    quantity = self.player.inventory.quantities.get(item_id, 0)
                    if quantity > 0:
                        self.ui.display_text(f"• {item.name} (x{quantity})")
            
            # Add a demo item for tutorial purposes
            self.ui.display_text("\nFor tutorial purposes, a sample item has been added to your inventory.")
            if self.resource_manager:
                food_item = self.resource_manager.get_random_item_by_category("food")
                if food_item:
                    self.player.add_item(food_item, 1)
                    self.ui.display_success(f"Added: {food_item.name}")
            
        elif interaction == "demo_use_item":
            try:
                if hasattr(self.player, 'inventory') and self.player.inventory.items:
                    # Find a food item to demonstrate
                    food_items = []
                    for item_id, item in self.player.inventory.items.items():
                        try:
                            # Check if item has required attributes
                            if hasattr(item, 'category') and getattr(item, 'category', None) and hasattr(item.category, 'value') and item.category.value == "food":
                                quantity = self.player.inventory.quantities.get(item_id, 0)
                                if quantity > 0:
                                    food_items.append((item_id, item))
                        except AttributeError:
                            continue
                    
                    if food_items:
                        item_id, item = food_items[0]
                        self.ui.display_subtitle(f"Using Item: {item.name}")
                        self.ui.display_text("When you use items, they can affect your stats or provide other benefits.")
                        safe_input("Press Enter to use this food item...")
                        
                        # Simulate using the item
                        try:
                            old_satiety = self.player.satiety
                            if hasattr(self.player, 'use_item'):
                                success, message = self.player.use_item(item_id)
                                
                                if success:
                                    self.ui.display_success(message)
                                    self.ui.display_text(f"Satiety before: {old_satiety}, Satiety after: {self.player.satiety}")
                                else:
                                    self.ui.display_error(f"Couldn't use item: {message}")
                            else:
                                self.ui.display_text("Item usage simulation complete.")
                        except Exception as e:
                            self.ui.display_text("Item usage simulation complete.")
                    else:
                        # No food item found
                        self.ui.display_subtitle("Using Items")
                        self.ui.display_text("You don't have any food items to demonstrate.")
                        self.ui.display_text("In the real game, you'll need to find or buy items to use them.")
                        self.ui.display_warning("No usable items in inventory for demonstration.")
                else:
                    self.ui.display_subtitle("Using Items")
                    self.ui.display_text("You don't have any items to demonstrate right now.")
                    self.ui.display_text("In the real game, you'll need to find or buy items to use them.")
                    self.ui.display_warning("No inventory items available for demonstration.")
            except Exception as e:
                self.ui.display_subtitle("Using Items")
                self.ui.display_text("Items can affect your stats or provide special benefits when used.")
                self.ui.display_text("In the real game, you'll need to find or buy items to use them.")
                
        elif interaction == "demo_travel":
            self.ui.display_subtitle("Travel System")
            self.ui.display_text("Traveling between locations takes time and energy, but gives access to different resources.")
            
            # Show sample locations
            sample_locations = [
                {"name": "Downtown Ottawa", "description": "Urban center with services and opportunities", "travel_time": 2},
                {"name": "Byward Market", "description": "Food sources and possible work", "travel_time": 1},
                {"name": "Rideau Centre", "description": "Shopping mall with shelter from weather", "travel_time": 1}
            ]
            
            self.ui.display_text("\nSample Available Destinations:")
            for i, loc in enumerate(sample_locations, 1):
                self.ui.display_text(f"{i}. {loc['name']} - {loc['description']} ({loc['travel_time']} hour travel)")
                
            self.ui.display_text("\nIn the actual game, you'll select a destination and travel there.")
            self.ui.display_text("This will advance game time and potentially trigger travel events.")
            
        elif interaction == "demo_services":
            self.ui.display_subtitle("Accessing Services")
            self.ui.display_text("Services provide essential assistance but have limited hours and availability.")
            
            # Show sample services
            sample_services = [
                {"name": "Shepherds of Good Hope", "type": "shelter", "hours": "5PM-8AM"},
                {"name": "Ottawa Food Bank", "type": "food_bank", "hours": "9AM-3PM"},
                {"name": "Community Health Clinic", "type": "medical", "hours": "10AM-4PM"}
            ]
            
            self.ui.display_text("\nSample Available Services:")
            for i, service in enumerate(sample_services, 1):
                self.ui.display_text(f"{i}. {service['name']} ({service['type']}) - Hours: {service['hours']}")
                
            self.ui.display_text("\nIn the actual game, you'll select a service to use if you're at the right location during operating hours.")
            
        elif interaction == "show_unlocked_features":
            self.ui.display_subtitle("Feature Availability System")
            
            try:
                # Display the player's currently unlocked features
                self.ui.display_text("Your currently unlocked features:")
                if hasattr(self.player, 'unlocked_features'):
                    for feature, unlocked in self.player.unlocked_features.items():
                        status = "✓ Available" if unlocked else "✗ Locked"
                        self.ui.display_text(f"• {feature.capitalize()}: {status}")
                else:
                    # Default feature set for tutorial if player doesn't have unlocked_features
                    default_features = {
                        "scavenging": True,
                        "shelters": True,
                        "food_banks": True,
                        "shops": False,
                        "crafting": False,
                        "work": False,
                        "black_market": False
                    }
                    for feature, unlocked in default_features.items():
                        status = "✓ Available" if unlocked else "✗ Locked"
                        self.ui.display_text(f"• {feature.capitalize()}: {status}")
            except Exception as e:
                # Provide default information if there's any error
                self.ui.display_text("Feature availability information is not available in tutorial mode.")
                
            self.ui.display_text("\nLocked features will become available as you progress.")
            self.ui.display_text("For example, shops unlock after surviving a few days, and crafting unlocks when you find suitable materials.")
            
        elif interaction == "show_skills":
            self.ui.display_subtitle("Skills & Abilities")
            
            try:
                # Display the player's starting skills
                self.ui.display_text("Your starting skills:")
                if hasattr(self.player, 'skills') and self.player.skills:
                    for skill_name, level in self.player.skills.items():
                        self.ui.display_text(f"• {skill_name.capitalize()}: Level {level}")
                else:
                    # Default skills for tutorial if player doesn't have skills attribute
                    default_skills = {
                        "survival": 2,
                        "social": 3,
                        "mechanical": 1,
                        "scavenging": 2,
                        "bartering": 1
                    }
                    for skill_name, level in default_skills.items():
                        self.ui.display_text(f"• {skill_name.capitalize()}: Level {level}")
            except Exception as e:
                # Provide default information if there's any error
                self.ui.display_text("Survival: Level 2")
                self.ui.display_text("Social: Level 1")
                self.ui.display_text("Street Smarts: Level 1")
                
            self.ui.display_text("\nSkills improve as you perform related activities.")
            self.ui.display_text("Higher skills increase success chances and unlock new opportunities.")
            
        elif interaction == "demo_scavenging":
            self.ui.display_subtitle("Scavenging Demonstration")
            self.ui.display_text("Scavenging lets you find items, but results vary by location and can take time.")
            
            safe_input("Press Enter to simulate scavenging...")
            
            # Simulate scavenging results
            self.ui.display_text("\nScavenging results:")
            
            # Generate sample results
            found_items = []
            if self.resource_manager:
                for _ in range(random.randint(1, 3)):
                    item = self.resource_manager.get_random_item()
                    if item:
                        found_items.append(item)
            
            if found_items:
                for item in found_items:
                    self.ui.display_success(f"• Found: {item.name}")
            else:
                self.ui.display_warning("Found nothing of value this time.")
                
            self.ui.display_text("\nIn the actual game, found items would be added to your inventory.")
            self.ui.display_text("Scavenging takes time and energy, and has risks in certain areas.")
            
        elif interaction == "demo_event":
            self.ui.display_subtitle("Random Event Demonstration")
            self.ui.display_text("Events occur as you explore and interact with the world.")
            
            # Sample event
            events = [
                {
                    "title": "Friendly Encounter",
                    "description": "You meet someone who offers to share information about local resources.",
                    "choices": ["Accept their help", "Politely decline", "Ask for food instead"]
                },
                {
                    "title": "Weather Change",
                    "description": "Dark clouds gather overhead. It looks like rain is coming soon.",
                    "choices": ["Find shelter quickly", "Continue what you're doing", "Look for rain protection"]
                },
                {
                    "title": "Police Patrol",
                    "description": "A police car slows down near you. The officer seems to be watching you.",
                    "choices": ["Act casual and keep walking", "Approach and ask for assistance", "Change direction and avoid them"]
                }
            ]
            
            event = random.choice(events)
            
            self.ui.display_text(f"\n{event['title']}")
            self.ui.display_text(f"{event['description']}")
            
            self.ui.display_text("\nChoices:")
            for i, choice in enumerate(event["choices"], 1):
                self.ui.display_text(f"{i}. {choice}")
                
            self.ui.display_text("\nIn the actual game, your choices during events will affect your character and story.")
            
        elif interaction == "demo_help":
            # Demonstrate the help system
            self.ui.display_subtitle("Help System Demonstration")
            self.ui.display_text("The help system provides contextual guidance based on your current situation.")
            
            # Show a mini version of the help screen
            self.ui.display_divider()
            self.ui.display_text("GAME HELP PREVIEW", "cyan")
            self.ui.display_text("")
            self.ui.display_text("Basic Controls:", "yellow")
            self.ui.display_text("• Enter numbers to select options")
            self.ui.display_text("• Press 'h' anytime for this help screen")
            self.ui.display_text("• Press Ctrl+C to quit the game")
            
            self.ui.display_text("")
            self.ui.display_text("Core Survival Tips:", "yellow")
            self.ui.display_text("• Always maintain your health above 25")
            self.ui.display_text("• Eat daily to keep satiety above 40")
            self.ui.display_text("• Find shelter during bad weather")
            
            self.ui.display_divider()
            self.ui.display_text("During the game, press 'h' at any time to access the full help system.")
            
    def show_tip(self, tip_id):
        """Show a contextual tip to the player if it hasn't been shown before."""
        if tip_id in self.gameplay_tips and tip_id not in self.tips_shown:
            self.ui.display_divider()
            self.ui.display_text(self.gameplay_tips[tip_id])
            self.ui.display_divider()
            self.tips_shown.add(tip_id)
            return True
        return False
            
    def _generate_progress_bar(self, percent, width=20):
        """Generate a visual progress bar.
        
        Args:
            percent (float): Percentage completed (0-100)
            width (int): Width of the progress bar in characters
            
        Returns:
            str: A text-based progress bar
        """
        # Validate inputs
        try:
            percent = float(percent)
        except (TypeError, ValueError):
            percent = 0.0
            
        # Ensure percent is within valid range
        percent = max(0.0, min(100.0, percent))
        
        # Ensure width is at least 1
        width = max(1, int(width))
        
        # Calculate filled portion
        filled = int((percent / 100.0) * width) if percent > 0 else 0
        # Ensure we don't exceed width
        filled = min(filled, width)
        bar = '█' * filled + '░' * (width - filled)
        return bar
        
    def _update_progress(self):
        """Update the overall tutorial progress based on section weights."""
        total_weight = sum(section["weight"] for section in self.sections_completed.values())
        completed_weight = sum(section["weight"] for section in self.sections_completed.values() 
                              if section["completed"])
        
        if total_weight > 0:
            self.tutorial_progress = (completed_weight / total_weight) * 100
        else:
            self.tutorial_progress = 0
            
    def _display_completion_certificate(self):
        """Display a visual certificate of tutorial completion."""
        certificate = [
            "╔══════════════════════════════════════════════════════╗",
            "║                                                      ║",
            "║             TUTORIAL COMPLETION CERTIFICATE          ║",
            "║                                                      ║",
            "║       This certifies that DEVIN has successfully     ║",
            "║          completed the Hard Times: Ottawa            ║",
            "║                 survival training                    ║",
            "║                                                      ║",
            "║                                                      ║",
            "║  You're now equipped with the knowledge needed to    ║",
            "║            survive on Ottawa's streets               ║",
            "║                                                      ║",
            "╚══════════════════════════════════════════════════════╝"
        ]
        
        for line in certificate:
            self.ui.display_text(line, "green")
        
        # Display mini-achievement stats
        self.ui.display_text("\nACHIEVEMENTS:", "yellow")
        self.ui.display_text("✓ Learned survival mechanics", "green")
        self.ui.display_text("✓ Practiced item management", "green")
        self.ui.display_text("✓ Explored the map system", "green")
        self.ui.display_text("✓ Understood service usage", "green")

    def show_help(self):
        """Show context-sensitive help based on player's situation."""
        try:
            current_time = time.time()
            
            # Avoid help spam by checking time since last help
            if current_time - self.last_help_timestamp < 10:  # 10 second cooldown
                return
                
            self.last_help_timestamp = current_time
            
            self.ui.clear_screen()
            self.ui.display_title("GAME HELP")
            
            # Basic help section
            self.ui.display_subtitle("Basic Controls:")
            self.ui.display_text("• Enter numbers to select options")
            self.ui.display_text("• Press 'h' anytime for this help screen")
            self.ui.display_text("• Press Ctrl+C to quit the game")
            
            # Core mechanics
            self.ui.display_subtitle("Core Survival Tips:")
            self.ui.display_text("• Always maintain your health above 25")
            self.ui.display_text("• Eat daily to keep satiety above 40")
            self.ui.display_text("• Rest when energy drops below 30")
            self.ui.display_text("• Find shelters during bad weather")
            self.ui.display_text("• Check service operating hours before traveling")
            
            # Current goals reminder
            self.ui.display_subtitle("Current Goals:")
            self.ui.display_text("• Find food and shelter for today")
            self.ui.display_text("• Discover more locations")
            self.ui.display_text("• Build relationships with helpful NPCs")
            self.ui.display_text("• Work toward stable housing and employment")
            
            # Let player return to game
            self.ui.display_divider()
            safe_input("Press Enter to return to the game...")
            self.ui.clear_screen()
        except Exception as e:
            from game.error_handler import error_handler
            error_handler.handle_error(e, {"action": "display_help"})
            print("There was an error displaying help. Press Enter to return to the game...")
            input()  # Use basic input as fallback
            try:
                self.ui.clear_screen()
            except:
                pass
        
    def check_for_tips(self, player, location, time_system):
        """Check if any contextual tips should be shown based on current game state."""
        # Check for critical stat warnings
        if player.health < 25:
            self.show_tip("low_health")
        if player.satiety < 20:
            self.show_tip("low_satiety")
        if player.energy < 20:
            self.show_tip("low_energy")
        if player.mental < 30:
            self.show_tip("low_mental")
        if player.hygiene < 25:
            self.show_tip("low_hygiene")
            
        # Check for weather warnings
        if time_system and hasattr(time_system, 'temperature'):
            if time_system.temperature < 5:
                self.show_tip("cold_weather")
            if time_system.weather in ["rain", "storm"]:
                self.show_tip("rain_warning")
                
        # Check for feature unlocks
        try:
            if hasattr(player, 'unlocked_features'):
                for feature, unlocked in player.unlocked_features.items():
                    if unlocked and f"feature_unlock_{feature}" not in self.tips_shown:
                        self.show_tip(f"feature_unlock_{feature}")
        except Exception:
            # Skip feature unlock tips if there's an error
            pass
