
"""Social services system handling welfare, disability support and food banks."""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random

class SocialServices:
    def __init__(self):
        self.applications = {}
        self.food_bank_visits = {}
        self.support_programs = {
            "welfare": {
                "base_amount": 700,
                "review_period": 30,
                "requirements": ["id_card"]
            },
            "disability": {
                "base_amount": 1200,
                "review_period": 60,
                "requirements": ["id_card", "medical_assessment"]
            }
        }
        
    def apply_for_welfare(self, player) -> tuple[bool, str]:
        """Apply for welfare assistance."""
        if "welfare" in self.applications:
            return False, "Already have a pending welfare application"
            
        if not player.has_item("id_card"):
            return False, "Need valid ID to apply for welfare"
            
        # Calculate approval chance based on multiple factors
        base_chance = 0.6
        if player.hygiene > 50:
            base_chance += 0.1
        if player.housing_status != "homeless":
            base_chance += 0.2
        
        # Economic factors affect approval chances
        if economy_manager and economy_manager.global_economy < 0.4:
            base_chance += 0.15  # More likely to be approved during economic downturns
        
        # Consider employment history
        if player.job_history and len(player.job_history) > 0:
            base_chance += 0.1
            
        # Consider previous application attempts
        if "previous_applications" in player.story_flags:
            base_chance += 0.05 * player.story_flags["previous_applications"]
            
        self.applications["welfare"] = {
            "submitted_date": datetime.now(),
            "review_period": 30,
            "approval_chance": base_chance,
            "status": "pending"
        }
        
        return True, "Welfare application submitted. Check back in 30 days."
        
    def apply_for_disability(self, player) -> tuple[bool, str]:
        """Apply for disability support."""
        if "disability" in self.applications:
            return False, "Already have a pending disability application"
            
        if not all(player.has_item(req) for req in self.support_programs["disability"]["requirements"]):
            return False, "Need ID and medical assessment for disability application"
            
        # Calculate approval chance
        base_chance = 0.4  # Harder to get approved
        if player.has_mental_illness:
            base_chance += 0.3
        if player.health < 50:
            base_chance += 0.2
            
        self.applications["disability"] = {
            "submitted_date": datetime.now(),
            "review_period": 60,
            "approval_chance": base_chance,
            "status": "pending"
        }
        
        return True, "Disability support application submitted. Check back in 60 days."
        
    def visit_food_bank(self, player) -> tuple[bool, str, Dict]:
        """Visit food bank for supplies."""
        last_visit = self.food_bank_visits.get(player.name)
        if last_visit and (datetime.now() - last_visit).days < 7:
            return False, "Can only visit food bank once per week.", {}
            
        # Calculate amount of food given
        base_items = {
            "Food": random.randint(2, 4),
            "Canned Food": random.randint(1, 3)
        }
        
        # Additional items based on need
        if player.satiety < 20:  # Very hungry (equivalent to old hunger > 80)
            base_items["Food"] += 1
        if player.has_mental_illness:
            base_items["Canned Food"] += 1
            
        self.food_bank_visits[player.name] = datetime.now()
        
        return True, "Received food bank assistance.", base_items
        
    def check_applications(self, player) -> List[str]:
        """Process pending social service applications."""
        messages = []
        for program, application in list(self.applications.items()):
            if application["status"] == "pending":
                days_pending = (datetime.now() - application["submitted_date"]).days
                
                if days_pending >= application["review_period"]:
                    if random.random() < application["approval_chance"]:
                        application["status"] = "approved"
                        
                        # Grant benefits
                        if program == "welfare":
                            amount = self.support_programs[program]["base_amount"]
                            player.money += amount
                            messages.append(f"Your welfare application was approved! You received ${amount}.")
                        elif program == "disability":
                            amount = self.support_programs[program]["base_amount"]
                            player.money += amount
                            messages.append(f"Your disability support application was approved! You received ${amount}.")
                            
                        player.dignity += 10
                        player.mental += 15
                    else:
                        application["status"] = "rejected"
                        messages.append(f"Your {program} application was rejected.")
                        player.mental -= 10
                        player.dignity -= 5
                        
        return messages


    def process_benefits(self, player, economy_manager=None):
        """Process and distribute regular benefit payments."""
        messages = []
        current_date = datetime.now()
        
        for program, application in self.applications.items():
            if application["status"] == "approved":
                last_payment = application.get("last_payment_date")
                if not last_payment or (current_date - last_payment).days >= 30:
                    amount = self.support_programs[program]["base_amount"]
                    
                    # Adjust amount based on economic conditions
                    if economy_manager:
                        if economy_manager.global_economy < 0.4:
                            amount *= 1.1  # 10% increase during economic hardship
                        elif economy_manager.global_economy > 0.8:
                            amount *= 0.9  # 10% decrease during economic boom
                    
                    player.money += amount
                    application["last_payment_date"] = current_date
                    messages.append(f"Received ${amount:.2f} from {program} benefits.")
                    
                    # Track economic impact
                    if economy_manager:
                        local_area = player.current_location
                        if local_area in economy_manager.local_demand:
                            economy_manager.local_demand[local_area] += 0.1
                            
        return messages
