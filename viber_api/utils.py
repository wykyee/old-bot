from os.path import basename
from typing import Union
from urllib.parse import urlsplit
from urllib.request import urlretrieve, urlcleanup

from django.db.models import QuerySet
from django.core.files import File
from django.conf import settings

from bots_management.models import Channel
from keyboards.models import Keyboard, Action
from keyboards.services import (
    get_button_and_joined_action,
    get_action_by_name
)
from subscribers.models import Message
from subscribers.services import get_subscriber_viber

# This message will send to the subscriber
# if the bot receives unknown text or action
default_message = "Обреріть, будь ласка, що Вас цікавить. " \
                  "(у разі необхідності допомоги почніть " \
                  "повідомлення з '/help')"


def create_text_message(uid: Union[str, list],
                        text: str, keyboard: Keyboard) -> dict:
    """
    uid: id or list(id) of receiver(s)
    text: text is gonna be sent
    keyboard: keyboard that user will see
    also can send message without keyboards
    """
    text_message = {
        "min_api_version": 1,
        "type": "text",
        "text": text,
    }
    if isinstance(uid, str):
        text_message['receiver'] = uid
    else:
        text_message['broadcast_list'] = uid
    try:
        keyboard = keyboard.get_keyboard_params()
    except AttributeError:
        pass
    if keyboard and keyboard.get('Buttons'):
        text_message['keyboard'] = keyboard
    return text_message


def save_message(channel: Channel,
                 in_data: dict,
                 is_help_message: bool = False) -> None:
    """
    Save message from subscribers in database
    """
    if not channel:
        raise ValueError("How did it happen?? 0_0")

    message_token = in_data["message_token"]
    subscriber, _ = get_subscriber_viber(
        user=in_data["sender"],
        channel=channel
    )

    message = in_data["message"]
    message_instance = Message(sender=subscriber, message_token=message_token)

    try:
        text = message["text"]
        message_instance.text = text
    except KeyError:
        pass

    try:
        media_url = message["media"]
        message_instance.url = media_url
    except KeyError:
        pass

    if channel.is_media_allowed:
        if message["type"] in ["picture", "sticker"]:
            download_to_file_field(url=message_instance.url,
                                   field=message_instance.image)
        elif message["type"] in ["video", "file"]:
            download_to_file_field(url=message_instance.url,
                                   field=message_instance.file)

    if all([message["type"] == "location",
            channel.is_geo_allowed]):
        message_instance.location = message["location"]

    if is_help_message:
        message_instance.is_help_message = True

    message_instance.save()


def download_to_file_field(url: str, field) -> None:
    """
    Download file from url
    """
    try:
        name, _ = urlretrieve(url)
        field.save(basename(urlsplit(url).path), File(open(name, 'rb')))
    finally:
        urlcleanup()


def get_action(in_data: dict, channel: Channel) -> Action:
    """
    Find action in response to a message
    """
    if in_data["message"]["type"] == "text":
        user_text: str = in_data["message"]["text"]

        tag: QuerySet = get_button_and_joined_action(user_text,
                                                     channel_slug=channel.slug)
        actions = get_action_by_name(user_text, channel_slug=channel.slug)

        if tag.exists():
            action: Action = tag.first().action
        elif actions.exists():
            action = actions.first()
        else:
            action: Action = set_default_message(channel)
    else:
        action: Action = set_default_message(channel)
    return action


def set_default_message(channel: Channel) -> Action:
    """
    set default message for welcome message
    """
    action: Action = channel.welcome_action
    if action:
        action.text = default_message
    return action


def get_data_for_message(action: Action, data: dict) -> dict:
    """
    Prepare data for messages from action
    """
    action_type: str = action.action_type
    data["type"] = action_type
    url = f"https://{settings.ALLOWED_HOSTS[0]}"
    print(url)
    if action_type == "picture" and action.picture:
        data["media"] = url + action.picture.url
        print(data["media"])
    elif action_type == "url" and action.url:
        data["media"] = action.url
    elif action_type == "video" and action.video:
        data["media"] = url + action.video.url
        data["size"] = action.video.size
    elif action_type == "file" and action.file:
        data["media"] = url + action.file.url
        data["file_name"] = str(action.file)
        data["size"] = action.file.size
        print(data["media"])
    elif all([action_type == "location",
              action.location_latitude,
              action.location_longitude]):
        data["location"] = {"lat": action.location_latitude,
                            "lon": action.location_longitude}
    elif action_type == "sticker":
        sticker_id = action.sticker_id
        if sticker_id:
            sticker_id = sticker_id.split('//')[0]
            data["sticker_id"] = sticker_id
    return data
