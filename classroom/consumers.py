import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import AttendanceLog


class SessionConsumer(AsyncWebsocketConsumer):
    """
    Sends:
      {"action": "init", "roster": ["s24ab12", "s24cd34"]}
      {"action": "add",  "user":   "s24ef56"}
    """

    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["pk"]
        self.group_name = f"sess_{self.session_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # initial roster
        rows = AttendanceLog.objects.filter(session_id=self.session_id)\
                                    .select_related("student__user")
        roster = [r.student.user.username for r in rows]
        await self.send(json.dumps({"action": "init", "roster": roster}))

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # event handler invoked by group_send in views.py
    async def attendance_event(self, event):
        await self.send(json.dumps(event["payload"]))
