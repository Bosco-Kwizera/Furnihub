from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Subscriber, NewsletterCampaign
from .forms import SubscriberForm

def subscribe(request):
    """Handle newsletter subscription"""
    if request.method == 'POST':
        form = SubscriberForm(request.POST)
        if form.is_valid():
            subscriber = form.save(commit=False)
            
            # Set source based on where subscription came from
            source = request.POST.get('source', 'website')
            subscriber.source = source
            subscriber.save()
            
            # Send welcome email
            send_welcome_email(subscriber.email, subscriber.name)
            
            messages.success(request, 'Successfully subscribed to our newsletter!')
            return redirect(request.META.get('HTTP_REFERER', 'products:home'))
        else:
            for error in form.errors.values():
                messages.error(request, error)
    
    return redirect('products:home')


def unsubscribe(request):
    """Handle newsletter unsubscription"""
    email = request.GET.get('email')
    if email:
        try:
            subscriber = Subscriber.objects.get(email=email, is_active=True)
            subscriber.unsubscribe()
            messages.success(request, 'You have been unsubscribed from our newsletter.')
        except Subscriber.DoesNotExist:
            messages.info(request, 'Email not found in our subscriber list.')
    
    return render(request, 'newsletter/unsubscribe.html')


def send_welcome_email(email, name=''):
    """Send welcome email to new subscriber"""
    subject = 'Welcome to FurniHub Newsletter!'
    
    context = {
        'name': name or 'there',
        'email': email,
        'unsubscribe_link': f"http://127.0.0.1:8000/unsubscribe/?email={email}"
    }
    
    html_message = render_to_string('emails/welcome.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=html_message,
        fail_silently=False,
    )


@staff_member_required
def campaign_list(request):
    """Admin view for newsletter campaigns"""
    campaigns = NewsletterCampaign.objects.all()
    return render(request, 'admin_dashboard/campaign_list.html', {'campaigns': campaigns})


@staff_member_required
def create_campaign(request):
    """Create and send newsletter campaign"""
    if request.method == 'POST':
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        
        campaign = NewsletterCampaign.objects.create(
            subject=subject,
            content=content,
            html_content=content,
            status='sent'
        )
        
        # Send campaign
        campaign.send()
        
        messages.success(request, f'Campaign "{subject}" sent to {campaign.sent_count} subscribers!')
        return redirect('newsletter:campaign_list')
    
    return render(request, 'admin_dashboard/create_campaign.html')