from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Track subscription source
    source = models.CharField(max_length=50, default='website', choices=[
        ('website', 'Website Footer'),
        ('checkout', 'Checkout Page'),
        ('popup', 'Popup'),
        ('account', 'Account Settings'),
    ])
    
    class Meta:
        ordering = ['-subscribed_at']
        verbose_name = 'Subscriber'
        verbose_name_plural = 'Subscribers'
    
    def __str__(self):
        return self.email
    
    def unsubscribe(self):
        self.is_active = False
        self.save()


class NewsletterCampaign(models.Model):
    subject = models.CharField(max_length=200)
    content = models.TextField()
    html_content = models.TextField(blank=True, help_text="HTML version for rich emails")
    
    # Status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('scheduled', 'Scheduled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Scheduling
    scheduled_for = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    sent_count = models.PositiveIntegerField(default=0)
    opened_count = models.PositiveIntegerField(default=0)
    clicked_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.subject
    
    def send(self):
        """Send campaign to all active subscribers"""
        from django.core.mail import send_mass_mail
        from django.conf import settings
        
        subscribers = Subscriber.objects.filter(is_active=True)
        messages = []
        
        for subscriber in subscribers:
            # Personalize content
            personalized_content = self.html_content.replace('{{name}}', subscriber.name or 'there')
            personalized_content = personalized_content.replace('{{email}}', subscriber.email)
            personalized_content = personalized_content.replace('{{unsubscribe_link}}', f"https://furnihub.com/unsubscribe/?email={subscriber.email}")
            
            messages.append(
                (self.subject, personalized_content, settings.DEFAULT_FROM_EMAIL, [subscriber.email])
            )
        
        if messages:
            send_mass_mail(messages, fail_silently=False)
            self.status = 'sent'
            self.sent_at = timezone.now()
            self.sent_count = len(messages)
            self.save()
            return True
        return False


class NewsletterTracking(models.Model):
    subscriber = models.ForeignKey(Subscriber, on_delete=models.CASCADE)
    campaign = models.ForeignKey(NewsletterCampaign, on_delete=models.CASCADE)
    opened = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['subscriber', 'campaign']