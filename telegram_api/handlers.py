import logging
from typing import Union

from django.conf import settings
from telebot.types import Message

from bots_management.models import Channel
from keyboards.models import Action, Keyboard
from keyboards.services import (
    get_home_action, get_emergency_action
)
from bots_management.services import get_channel_by_slug
from .api import (
    send_message
)
from .utils import (
    create_markup, save_message,
    get_action, send_message_with_media, create_inline_markup
)
from subscribers.services import get_subscriber_telegram


logger = logging.getLogger(__name__)


def event_handler_tg(incoming_data: dict, channel_slug: str) -> None:
    """
    main handler
    """
    channel = get_channel_by_slug(slug=channel_slug)
    message = incoming_data.get("message")
    if message:
        uid = message["chat"]["id"]
        need_action = True
        if 'text' in message:
            if message.get("text") == "/start":
                subscribed_handler(
                    in_data=incoming_data, channel=channel
                )
                need_action = False
            elif message.get("text").startswith("/"):
                sys_action_handler(
                    in_data=incoming_data, channel_slug=channel_slug
                )
                need_action = False
        if need_action:
            action = get_action(incoming_data, channel)
            action_handler(
                uid=uid,
                channel=channel,
                action=action
            )

        if settings.SAVE_MESSAGE:
            save_message(channel=channel, in_data=incoming_data)

    else:
        # for example it can be "edited_message"
        # TODO now we don't do anything with it
        return


def action_handler(uid: str, channel: Channel, action: Action) -> list:
    """
        Prepare data for message and send answer message
        separate sending media and text (if they are in one action)
    """
    data = {
        'token': channel.telegram_token,
        'chat_id': uid,
    }
    response = []
    if action:
        action_type: str = action.action_type
        data['action'] = action
        data['reply_markup'] = create_markup(action)
        # add it for example, TODO in future finish this
        if action.name == 'Виклик 102':
            data['reply_markup'] = create_inline_markup(action)
        if action_type != "text":
            response.append(send_message_with_media(data, action))
        if action.text:
            # data['reply_markup'] = create_markup(action)
            response.append(send_message(
                **data,
                text=action.text,
            ))
    else:
        response.append(send_message(
            **data,
            text="No welcome action",
        ))
    return response


def help_message_handler(in_data: dict, channel_slug: str) -> None:
    """
    Sends message to user, that his help message was sent and
    moderator will contact him
    """
    # TODO create help message and send notification to moderator

    action: Union[Action, None] = get_emergency_action(
        channel_slug=channel_slug
    )

    if not action:
        action: Action = get_home_action(slug=channel_slug)

    keyboard: Keyboard = action.keyboard_to_represent

    send_message(
        chat_id=in_data["message"]["chat"]["id"],
        text=action.text,
        reply_markup=create_markup(action),
        token=keyboard.channel.telegram_token
    )


def sys_action_handler(in_data: dict, channel_slug: str) -> None:
    """
        handler for command starts with '/'
    """
    if in_data["message"]["text"][:5].upper() == "/HELP":
        help_message_handler(in_data=in_data, channel_slug=channel_slug)
        save_message(channel=get_channel_by_slug(channel_slug),
                     in_data=in_data,
                     is_help_message=True)
    # TODO if other system commands add elif
    else:
        action: Action = get_home_action(slug=channel_slug)
        keyboard: Keyboard = action.keyboard_to_represent
        send_message(
            chat_id=in_data["message"]["chat"]["id"],
            text=action.text,
            reply_markup=create_markup(action),
            token=keyboard.channel.telegram_token
        )


def subscribed_handler(in_data: dict, channel: object) -> None:
    """
        Handler for saving new/returned subscribers
    """
    user = in_data.get('message').get('chat')
    subscraber, created = get_subscriber_telegram(user, channel)
    logger.warning(
        f"""Subscraber {subscraber} create new {created} (False=update)"""
    )

    start_action = channel.welcome_action
    if start_action:
        action_handler(user.get('id'), channel, start_action)
    else:
        logger.warning('No welcome action')
        send_message(
            chat_id=subscraber.user_id,
            text='No welcome action',
            token=channel.telegram_token
        )
