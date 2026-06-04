from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def chat_timestamp(value):
    if not value:
        return ""

    local_time = timezone.localtime(value)
    now = timezone.localtime(timezone.now())
    time_str = local_time.strftime("%I:%M %p").lstrip("0").lower()

    if local_time.date() == now.date():
        return f"Today {time_str}"

    weekday = local_time.strftime("%A")
    return f"{weekday} {time_str}"
