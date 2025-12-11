from django.urls import path
from . import views 

app_name = 'payments'

urlpatterns = [
    path('ready/', views.subscription_ready, name='sub_ready'),
    path('approve/', views.subscription_approve, name='sub_approve'),
    path("cancel_subscription", views.cancel_subscription, name="cancel_subscription"),
    path("renew_subscription", views.renew_subscription, name="renew_subscription")
]