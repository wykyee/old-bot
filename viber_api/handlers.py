import logging
from typing import Union

from django.conf import settings

from bots_management.models import Channel
from bots_management.services import (
    get_channel_by_slug,
)
from keyboards.models import Action, Keyboard
from keyboards.services import (
    get_home_action,
    get_emergency_action,
)
from subscribers.models import Subscriber
from subscribers.services import (
    get_subscriber_viber
)
from .api import send_message
from .utils import (
    create_text_message, save_message,
    get_data_for_message, get_action
)

logger = logging.getLogger(__name__)


def event_handler(incoming_data: dict, channel_slug: str) -> None:
    """
    main handler
    """
    event: str = incoming_data.get("event")
    if not event:
        return
    channel = get_channel_by_slug(slug=channel_slug)

    if event == "message":
        message = incoming_data.get("message")
        if message:
            if (message.get("type") == "text" and
                    message.get("text").startswith("/")):
                sys_action_handler(in_data=incoming_data,
                                   channel=channel)
            else:
                action = get_action(incoming_data, channel)
                action_handler(uid=incoming_data["sender"]["id"],
                               token=channel.viber_token,
                               action=action)

            if settings.SAVE_MESSAGE:
                save_message(channel=channel, in_data=incoming_data,
                             is_help_message=False)

    elif event in ["conversation_started", "subscribed"]:
        subscribed_handler(in_data=incoming_data,
                           channel=channel)

    elif event == "unsubscribed":
        unsubscribed_handler(in_data=incoming_data,
                             channel=channel)

    elif event == "failed":
        logger.error(f'Error delivered message Viber {incoming_data}')

    elif event in ["delivered", "seen"]:
        pass


def action_handler(uid: Union[str, list],
                   token: str, action: Action = None,
                   broadcast: bool = False) -> None:
    """
    Prepare data for message and send answer message
    separate sending media and text (if it in one action)
    """
    data = dict()
    if isinstance(uid, str):
        data['receiver'] = uid
    else:
        data['broadcast_list'] = uid

    if action:
        keyboard: Keyboard = action.keyboard_to_represent
        data['min_api_version'] = 1
        data['keyboard'] = keyboard.get_keyboard_params()
        action_type: str = action.action_type
        if action_type != "text":
            data = get_data_for_message(action, data)
            if action_type != "none":
                send_message(data, token, broadcast)
        if action.text:
            text_message: dict = create_text_message(
                uid=uid,
                text=action.text,
                keyboard=keyboard.get_keyboard_params()
            )
            send_message(text_message, token, broadcast)
    else:
        text_message: dict = create_text_message(
            uid=uid,
            text="No welcome action",
            keyboard=None
        )
        send_message(text_message, token, broadcast)


def help_message_handler(in_data: dict, channel: Channel) -> None:
    """
    Sends message to user, that his help message was sent and
    moderator will contact him
    """
    # TODO create help message and send notification to moderator

    logger.warning(f"HELP MESSAGE: {in_data}")
    action: Union[Action, None] = get_emergency_action(
        channel_slug=channel.slug
    )

    if not action:
        action: Action = get_home_action(slug=channel.slug)

    keyboard: Keyboard = action.keyboard_to_represent

    text_message: dict = create_text_message(uid=in_data["sender"]["id"],
                                             text=action.text,
                                             keyboard=keyboard)

    send_message(text_message, channel.viber_token)


def sys_action_handler(in_data: dict, channel: Channel) -> None:
    """
    handler for command starts with '/'
    """
    if in_data["message"]["text"][:5].upper() == "/HELP":
        help_message_handler(in_data=in_data, channel=channel)

        save_message(channel=channel, in_data=in_data,
                     is_help_message=True)
    # TODO if other system commands add elif
    else:
        action: Action = get_home_action(slug=channel.slug)
        keyboard: Keyboard = action.keyboard_to_represent

        text_message: dict = create_text_message(uid=in_data["sender"]["id"],
                                                 text=action.text,
                                                 keyboard=keyboard)
        send_message(text_message, channel.viber_token)


def subscribed_handler(in_data: dict, channel: Channel) -> None:
    """
    Handler for saving new/returned subscribers
    """
    user = in_data.get('user')
    subscriber, created = get_subscriber_viber(user, channel)
    logger.warning(
        f"""Subscriber {subscriber} create new {created} (False=update)"""
    )

    start_action: Action = channel.welcome_action
    if start_action:
        action_handler(user.get('id'), channel.viber_token, start_action)
    else:
        logger.warning('No welcome action')
        text_message: dict = create_text_message(
            uid=in_data["user"]["id"],
            keyboard=None,
            text='No welcome action'
        )
        send_message(text_message, channel.viber_token)


def unsubscribed_handler(in_data: dict, channel: Channel) -> None:
    """
    When event unsubscribed, set is_active for user in False
    """
    subscriber = Subscriber.objects.filter(
        user_id=in_data.get('user_id'),
        messengers_bot=channel.viber_bot,
    )
    subscriber.update(is_active=False)
    logger.warning(
        f"""User {subscriber} unsubscribed (is_active=False)"""
    )
