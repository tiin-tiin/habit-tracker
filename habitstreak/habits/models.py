from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta

class Habit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habits')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=50, default='General') 
    created_date = models.DateField(default=timezone.now) 
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"
    
    def current_streak(self):
        checkins = self.checkins.filter(checked=True).order_by('-date')
        if not checkins.exists(): return 0
        today = date.today()
        latest = checkins.first().date
        if latest < today - timedelta(days=1): return 0
        streak = 0
        current_date = today if latest == today else today - timedelta(days=1)
        for checkin in checkins:
            if checkin.date == current_date:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        return streak
    
    def total_checkins(self):
        return self.checkins.filter(checked=True).count()
    
    def get_tree_stage(self):
        streak = self.current_streak()
        if streak == 0: return 'seed'
        elif streak <= 3: return 'sprout'
        elif streak <= 7: return 'sapling'
        elif streak <= 14: return 'young-tree'
        elif streak <= 30: return 'tree'
        else: return 'full-tree'

    class Meta:
        ordering = ['-created_date']

class CheckIn(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='checkins')
    date = models.DateField(default=date.today)
    checked = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.habit.name} - {self.date}"
    
    class Meta:
        unique_together = ('habit', 'date')
        ordering = ['-date']