from django.urls import path
from . import views

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Habit Management (Make sure these are here!)
    path('habits/manage/', views.manage_habits, name='manage_habits'),
    path('habits/add/', views.add_habit, name='add_habit'),
    path('habits/edit/<int:habit_id>/', views.edit_habit, name='edit_habit'),
    path('habits/delete/<int:habit_id>/', views.delete_habit, name='delete_habit'),
    
    # Month and Check-in views
    path('month/<int:year>/<int:month>/', views.month_view, name='month_view'),
    path('checkin/<int:year>/<int:month>/<int:day>/', views.daily_checkin, name='daily_checkin'),
    
    # AJAX validation endpoints
    path('ajax/validate-username/', views.validate_username, name='validate_username'),
    path('ajax/validate-email/', views.validate_email, name='validate_email'),
    
    # REST API endpoint
    path('api/toggle-checkin/', views.api_toggle_checkin, name='api_toggle_checkin'),
]