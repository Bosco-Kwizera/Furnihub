from django.contrib import admin
from .models import Subscriber

@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'is_active', 'subscribed_at', 'source']
    list_filter = ['is_active', 'source']
    search_fields = ['email', 'name']
    actions = ['unsubscribe_selected']
    
    def unsubscribe_selected(self, request, queryset):
        queryset.update(is_active=False)
    unsubscribe_selected.short_description = "Unsubscribe selected"