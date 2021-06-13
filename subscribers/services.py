from typing import Union

from django.db import ProgrammingError
from django.db.models import Q, QuerySet, Count

from bots_management.models import Bot, Channel
from .models import Subscriber, Message, HelpReply


# def get_subscriber(uid: str, bot: Bot) -> Union[Subscriber, None]:
#     return Subscriber.objects.filter(
#         Q(user_id=uid) & Q(messengers_bot=bot)
#     ).first()


def get_subscriber_viber(user: dict,
                         channel: Channel) -> Union[Subscriber, None]:
    return Subscriber.objects.update_or_create(
        user_id=user.get('id'),
        messengers_bot=channel.viber_bot,
        defaults={
            'user_id': user.get('id'),
            'name': user.get('name'),
            'avatar': user.get('avatar'),
            'is_active': True,
            'messengers_bot': channel.viber_bot
        }
    )


def get_subscriber_telegram(user: dict,
                            channel: Channel) -> Union[Subscriber, None]:
    username = user.get('username')
    if not username:
        username = user.get('first_name')
    return Subscriber.objects.update_or_create(
        user_id=user.get('id'),
        messengers_bot=channel.telegram_bot,
        defaults={
            'user_id': user.get('id'),
            'name': username,
            'is_active': True,
            'messengers_bot': channel.telegram_bot,
        }
    )


def get_all_active_subs(channel: Channel) -> QuerySet:
    return Subscriber.objects.filter(
        is_active=True, messengers_bot__channel=channel
    )


def get_subscribers_of_channel(slug: str) -> QuerySet:
    return Subscriber.objects.select_related(
        "messengers_bot", "messengers_bot__channel"
    ).filter(messengers_bot__channel__slug=slug)


def get_subscribers_of_messenger(
        slug: str, messenger: str = 'all') -> QuerySet:
    subscribers = get_subscribers_of_channel(slug)
    if messenger != 'all':
        subscribers = subscribers.filter(messengers_bot__messenger=messenger)
    return subscribers


def get_status_subscribers_of_messenger(
        slug: str, messenger: str = 'all',
        status: str = 'all') -> QuerySet:
    subscribers = get_subscribers_of_messenger(slug, messenger)
    if status != 'all':
        if status == 'active':
            subscribers = subscribers.filter(is_active=True)
        elif status == 'not_active':
            subscribers = subscribers.filter(is_active=True)
    return subscribers


def get_num_of_subs(channel: Channel) -> int:
    try:
        result = get_all_active_subs(channel).aggregate(
            Count('id')
        )["id__count"]
        return result
    except ProgrammingError:
        return 0


def get_num_of_subs_to_messenger(channel: Channel, messenger: str) -> int:
    try:
        result = get_all_active_subs(channel).filter(
            messengers_bot__messenger=messenger
        ).aggregate(Count('id'))["id__count"]
        return result
    except ProgrammingError:
        return 0


def get_messages_subscribers_of_channel(slug: str,
                                        messenger: str = 'all') -> QuerySet:
    senders = get_subscribers_of_messenger(slug, messenger)
    messages = Message.objects.prefetch_related('sender').filter(
        sender__in=senders
    )
    return messages.order_by('-id')


def get_all_help_messages(slug: str) -> QuerySet:
    """
    Returns all messages, asking for help
    """
    return Message.objects.filter(
        is_help_message=True,
        sender__messengers_bot__channel__slug=slug,
    )


def get_all_active_help_messages(slug: str) -> QuerySet:
    """
    Returns all active messages, asking for help
    """
    return Message.objects.filter(
        is_help_message=True,
        sender__messengers_bot__channel__slug=slug,
        help_reply__is_started=False,
        help_reply__is_closed=False
    )


def get_all_started_help_messages(slug: str) -> QuerySet:
    """
    Returns all started messages, asking for help
    """
    return Message.objects.filter(
        is_help_message=True,
        sender__messengers_bot__channel__slug=slug,
        help_reply__is_started=True,
        help_reply__is_closed=False
    )


def get_all_closed_help_messages(slug: str) -> QuerySet:
    """
    Returns all closed messages, asking for help
    """
    return Message.objects.filter(
        is_help_message=True,
        sender__messengers_bot__channel__slug=slug,
        help_reply__is_closed=True
    )


def get_help_message_reply(pk: int) -> Union[HelpReply, None]:
    return HelpReply.objects.filter(pk=pk).first()


def is_telegram_subscriber(subscriber: Subscriber) -> bool:
    return subscriber.messengers_bot.messenger == "telegram"


def is_viber_subscriber(subscriber: Subscriber) -> bool:
    return subscriber.messengers_bot.messenger == "viber"
