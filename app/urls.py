# -*- encoding: utf-8 -*-

from django.urls import path
from app import views

urlpatterns = [
    path('', views.get_screenshot, name='get_screenshot'),
    path('v2', view.get_v2_screenshot, name='get_v2_screenshot')
]