import logging

from time import sleep

from telegram_api.api import (
    delete_message as tg_delete_message
)
from bots_mailings.models import Post, SentMessage
from bots_mailings.services import create_sent_message_object
from keyboards.models import Action
from viber_api.handlers import action_handler as v_action_handler
from telegram_api.handlers import action_handler as tg_action_handler

logger = logging.getLogger(__name__)


def send_action_to_telegram_user(
        chat_id: int, action: Action, post: Post) -> None:
    """
    Parse action due to it`s type
    and send message with provided content to chat_id
    """
    token = post.channel.telegram_token

    response = tg_action_handler(
        uid=chat_id,
        channel=post.channel,
        action=action
    )

    for message in response:
        if message:
            create_sent_message_object(
                chat_id=chat_id,
                message_id=message.message_id,
                post=post,
                action=action
            )


def send_action_to_telegram_users(
        subscriber_list: list, action: Action, post: Post) -> None:
    """
    Send action to all telegram subscribers in subscriber_list
    """
    for subscriber in subscriber_list:
        send_action_to_telegram_user(
            chat_id=subscriber,
            action=action,
            post=post
        )

        # Telegram API will not allow send more than 30 messages per second
        # to bypass blocking sleep thread for 0.5 secs
        # TODO: try to find more efficient way to bypass blocking
        sleep(0.1)


def delete_telegram_messages(messages:dict, token):
    """
    Delete all messages of the post in Telegram
    """

    for message_id, chat_id in messages.items():
        tg_delete_message(
            chat_id=chat_id,
            message_id=message_id,
            token=token
        )
        # Telegram API will not allow send more than 30 messages per second
        # to bypass blocking sleep thread for 0.5 secs
        # TODO: try to find more efficient way to bypass blocking
        sleep(0.1)


def broadcast_to_viber_users(
        broadcast_list: list, action: Action, token: str) -> None:
    """
    Parse action due to it`s type
    and send message with provided content to chat_id
    """
    uid = [subscriber for subscriber in broadcast_list]
    v_action_handler(
        uid=uid,
        token=token,
        action=action,
        broadcast=True,
    )


def send_action_to_viber_users(
        subscriber_list: list, action: Action,
        token: str, limit: int = 300) -> None:
    """
    Call broadcast_to_viber_users
    for every 300 receivers due to viber`s limitation
    """
    for i in range(len(subscriber_list) // limit + 1):
        broadcast_to_viber_users(
            broadcast_list=subscriber_list[i * limit:(i + 1) * limit],
            action=action,
            token=token
        )
