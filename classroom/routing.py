from django.urls import re_path
from .consumers import SessionConsumer

websocket_urlpatterns = [
    re_path(r"ws/session/(?P<pk>[0-9a-f-]+)/$", SessionConsumer.as_asgi()),
]
