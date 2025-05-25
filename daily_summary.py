
"""Daily summary system for tracking goals and progress."""

class DailySummary:
    def __init__(self, ui):
        self.ui = ui
        self.journal_entries = []
        self.active_goals = []
        self.completed_goals = []
        self.day_activities = []
        self.daily_stats = {
            'money_earned': 0,
            'money_spent': 0,
            'health_change': 0,
            'mental_change': 0,
            'energy_change': 0,
            'activities_completed': 0,
            'goals_achieved': 0
        }
        self.goal_progress = {}
        self.activity_categories = {
            'survival': [],
            'social': [], 
            'progress': [],
            'quest': []
        }

    def add_activity(self, activity_type, description, outcomes=None, category='survival'):
        """Record a daily activity with improved categorization."""
        activity = {
            'type': activity_type,
            'description': description,
            'outcomes': outcomes or {},
            'category': category
        }
        self.day_activities.append(activity)
        self.activity_categories[category].append(activity)
        self.daily_stats['activities_completed'] += 1
        self._track_outcomes(outcomes)

    def add_goal(self, goal, priority=2, quest_related=False, quest_id=None, deadline=None):
        """Add a goal with enhanced tracking."""
        if not any(g['description'] == goal for g in self.active_goals):
            goal_data = {
                'description': goal,
                'priority': priority,
                'completed': False,
                'quest_related': quest_related,
                'quest_id': quest_id,
                'progress': 0,
                'total': 100,
                'deadline': deadline,
                'creation_time': self.ui.time_system.get_time_string() if hasattr(self.ui, 'time_system') else None
            }
            self.active_goals.append(goal_data)
            self.goal_progress[goal] = 0
            return True, "Goal added successfully"
        return False, "Goal already exists"

    def update_goal_progress(self, goal_description, progress, total=100):
        """Update progress with validation and feedback."""
        try:
            if progress < 0 or progress > total:
                return False, "Invalid progress value"
                
            for goal in self.active_goals:
                if goal['description'] == goal_description:
                    old_progress = goal['progress']
                    goal['progress'] = progress
                    goal['total'] = total
                    self.goal_progress[goal_description] = (progress / total) * 100
                    
                    # Generate feedback message
                    if progress >= total:
                        self.complete_goal(goal_description)
                        return True, f"Goal completed: {goal_description}"
                    elif progress > old_progress:
                        return True, f"Progress made: {int((progress/total)*100)}% complete"
                        
            return False, "Goal not found"
        except Exception as e:
            return False, f"Error updating goal: {str(e)}"

    def complete_goal(self, goal_description):
        """Mark a goal as completed with rewards."""
        for goal in self.active_goals:
            if goal['description'] == goal_description:
                goal['completed'] = True
                goal['progress'] = goal['total']
                self.completed_goals.append(goal)
                self.active_goals.remove(goal)
                if goal_description in self.goal_progress:
                    del self.goal_progress[goal_description]
                self.daily_stats['goals_achieved'] += 1
                return True, "Goal completed successfully"
        return False, "Goal not found"

    def add_journal_entry(self, entry, entry_type="general"):
        """Add entry to player's journal with improved categorization."""
        self.journal_entries.append({
            'text': entry,
            'type': entry_type,
            'time': self.ui.time_system.get_time_string() if hasattr(self.ui, 'time_system') else None,
            'importance': 'high' if entry_type in ['milestone', 'quest'] else 'normal'
        })

    def _track_outcomes(self, outcomes):
        """Track daily stat changes with improved analytics."""
        if not outcomes:
            return

        if 'money' in outcomes:
            if outcomes['money'] > 0:
                self.daily_stats['money_earned'] += outcomes['money']
            else:
                self.daily_stats['money_spent'] += abs(outcomes['money'])

        for stat in ['health', 'mental', 'energy']:
            if stat in outcomes:
                self.daily_stats[f'{stat}_change'] += outcomes[stat]

    def display_summary(self, player, time_system):
        """Show enhanced daily summary with visual feedback."""
        self.ui.clear_screen()
        self.ui.display_title(f"Daily Summary - Day {time_system.get_day()}")
        self.ui.display_text(f"Time: {time_system.get_time_string()}")
        self.ui.display_divider()

        # Show urgent needs
        self._display_urgent_needs(player, time_system)
        
        # Display daily stats with enhanced visuals
        self._display_daily_stats()
        
        # Activity breakdown by category
        self._display_activity_breakdown()
        
        # Active goals with improved progress visualization
        if self.active_goals:
            self.ui.display_subtitle("Current Goals")
            for goal in sorted(self.active_goals, key=lambda g: (-g['priority'], g['description'])):
                prefix = "!" * goal['priority']
                progress_percent = (goal['progress'] / goal['total']) * 100
                
                # Color code based on progress
                if progress_percent >= 75:
                    color = "green"
                elif progress_percent >= 50:
                    color = "yellow"
                else:
                    color = "white"
                    
                if goal['quest_related']:
                    self.ui.display_text(f"{prefix} {goal['description']} (Quest)", color="yellow")
                else:
                    self.ui.display_text(f"{prefix} {goal['description']}", color=color)
                
                self.ui.progress_bar(goal['progress'], goal['total'], 
                                   title="Progress", animate=True)
        
        # Recent activities with categorization
        if self.day_activities:
            self.ui.display_subtitle("Today's Activities")
            for activity in self.day_activities[-5:]:
                category_colors = {
                    'survival': 'red',
                    'social': 'blue',
                    'progress': 'green',
                    'quest': 'yellow'
                }
                color = category_colors.get(activity['category'], 'white')
                self.ui.display_text(f"• [{activity['category']}] {activity['description']}", 
                                   color=color)
        
        # Progress indicators with enhanced visuals
        self._display_progress_indicators(player)
        
        # Achievement summary
        if self.completed_goals:
            self.ui.display_subtitle("Today's Achievements")
            for goal in self.completed_goals:
                self.ui.display_text(f"✓ {goal['description']}", color="green")
        
        self.ui.display_divider()

    def _display_activity_breakdown(self):
        """Display activity breakdown by category."""
        if sum(len(activities) for activities in self.activity_categories.values()) > 0:
            self.ui.display_subtitle("Activity Breakdown")
            for category, activities in self.activity_categories.items():
                if activities:
                    total = len(self.day_activities)
                    percent = (len(activities) / total) * 100 if total > 0 else 0
                    self.ui.progress_bar(len(activities), total, 
                                       title=f"{category.title()}", animate=False)

    def _display_urgent_needs(self, player, time_system):
        """Display urgent needs section with priority indicators."""
        urgent_needs = []
        if player.satiety < 30:
            urgent_needs.append(("URGENT: You need food!", "red", 1))
        if player.energy < 30:
            urgent_needs.append(("URGENT: You need rest!", "red", 1))
        if time_system.is_harsh_weather():
            urgent_needs.append(("URGENT: Find shelter from the weather!", "red", 1))
            
        if urgent_needs:
            self.ui.display_subtitle("⚠ Urgent Needs")
            for message, color, priority in sorted(urgent_needs, key=lambda x: x[2]):
                self.ui.display_text(message, color=color)
            self.ui.display_divider()

    def _display_daily_stats(self):
        """Display enhanced daily statistics with visual indicators."""
        if any(value != 0 for value in self.daily_stats.values()):
            self.ui.display_subtitle("Daily Statistics")
            if self.daily_stats['money_earned'] > 0:
                self.ui.display_text(f"💰 Money Earned: ${self.daily_stats['money_earned']:.2f}", 
                                   color="green")
            if self.daily_stats['money_spent'] > 0:
                self.ui.display_text(f"💸 Money Spent: ${self.daily_stats['money_spent']:.2f}", 
                                   color="red")
            
            for stat in ['health', 'mental', 'energy']:
                change = self.daily_stats[f'{stat}_change']
                if change != 0:
                    icon = "+" if change > 0 else "-"
                    color = "green" if change > 0 else "red"
                    self.ui.display_text(f"{icon} {stat.title()} Change: {change:+d}", 
                                       color=color)
            
            # Display activity and goal completion stats
            self.ui.display_text(f"📝 Activities Completed: {self.daily_stats['activities_completed']}")
            self.ui.display_text(f"🎯 Goals Achieved: {self.daily_stats['goals_achieved']}")
            self.ui.display_divider()

    def _display_progress_indicators(self, player):
        """Display enhanced progress indicators with visual feedback."""
        self.ui.display_subtitle("Progress Tracking")
        if hasattr(player, 'job_prospects') and player.job_prospects > 0:
            self.ui.progress_bar(player.job_prospects, 100, 
                               title="💼 Job Search", animate=True)
        if hasattr(player, 'housing_prospects') and player.housing_prospects > 0:
            self.ui.progress_bar(player.housing_prospects, 100, 
                               title="🏠 Housing Search", animate=True)
