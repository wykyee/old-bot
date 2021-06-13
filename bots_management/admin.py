from django.contrib import admin
from .models import Channel, Bot


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    pass


@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    pass
