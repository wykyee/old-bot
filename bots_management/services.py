import json
from typing import Union

from django.contrib.auth import get_user_model
from django.db.models import QuerySet, Q
from django.forms import model_to_dict

from .models import Channel, Bot


def get_channel_by_slug(slug: str) -> Union[Channel, None]:
    return Channel.objects.filter(slug=slug).first()


def get_all_available_channels_to_moderator(user) -> QuerySet:
    """
    Returns all available channels to moderator, or all
    channels to superuser.
    """
    if user.is_superuser:
        return Channel.objects.all()
    return user.channel_set.all()


def get_all_related_bots(channel: Channel) -> QuerySet:
    return channel.bots.all()


def get_all_bots() -> QuerySet:
    return Bot.objects.all()


def get_bot_to_channel(channel_slug: str, messenger: str) -> Union[Bot, None]:
    return Bot.objects.filter(
        Q(channel__slug=channel_slug) & Q(messenger=messenger)
    ).first()


# TODO add filter for moderators
def get_channel_to_json() -> json:  # it returns str btw
    channels = Channel.objects.all().select_related()
    channels = [model_to_dict(channel) for channel in channels]
    for channel in channels:
        channel['moderators'] = [
            model_to_dict(moderator).get('username')
            for moderator in channel['moderators']
        ]
    return json.dumps(channels)


# TODO find a better solution
def extract_data(request):
    """
    reformate js true/false in True/False
    """
    tmp = request.POST.dict()
    for key, value in tmp.items():
        if value == 'true':
            tmp[key] = True
        if value == 'false':
            tmp[key] = False
    return tmp


def get_moderators_to_json() -> json:   # it returns str btw
    moderators = get_user_model().objects.all()
    moderators = [{'name': moderator.username,
                   'id': moderator.id} for moderator in moderators]
    return json.dumps(moderators)
