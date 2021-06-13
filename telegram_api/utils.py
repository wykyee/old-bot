from os.path import basename
from urllib.parse import urlsplit
from urllib.request import urlretrieve, urlcleanup

from django.db.models import QuerySet
from telebot import TeleBot
from django.core.files import File

from keyboards.models import Action
from telebot.types import (
    KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from bots_management.models import Channel
from keyboards.services import (
    get_button_and_joined_action, get_action_by_name
)
from subscribers.models import Message
from subscribers.services import (
    get_subscriber_telegram
)
from telegram_api.api import (
    send_media, send_message,
    send_location, send_sticker
)
# This message will send to the subscriber
# if the bot receives unknown text or action
default_message = "Обреріть, будь ласка, що Вас цікавить. " \
                  "(у разі необхідності допомоги почніть " \
                  "повідомлення з '/help')"


def create_markup(action: Action) -> ReplyKeyboardMarkup:
    """
    Creates markup for the telegram keyboard.

    Returns:
        ReplyKeyboardMarkup that represents markup.
    """
    markup = ReplyKeyboardMarkup()
    btn_array = action.keyboard_to_represent.get_telegram_buttons()
    for row in btn_array:
        inline_btns = [
            KeyboardButton(
                text=btn.text,
            ) for btn in row
        ]
        markup.row(*inline_btns)
    return markup


def create_inline_markup(action: Action) -> InlineKeyboardButton:
    """
    Creates inline markup for the telegram keyboard.

    Returns:
        ReplyKeyboardMarkup that represents markup.

    It's added only for example TODO update it
    """
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton(
        "Виклик по телефону",
        url="http://tinyurl.com/vntqajk"
    ))
    return markup


def save_message(channel: Channel, in_data: dict,
                 is_help_message: bool = False) -> None:
    """
    Save massage info from telegram subscribers in db
    field what can be saved:
    ['document', 'photo', 'audio', 'video',
     'voice', 'sticker', 'text', 'caption', 'location']
    """
    if not channel:
        raise ValueError("How did it happen?? 0_0")
    message = in_data["message"]
    message_token = message.get('message_id')

    subscriber, _ = get_subscriber_telegram(
        user=message.get('chat'),
        channel=channel
    )
    message_instance = Message(sender=subscriber, message_token=message_token)
    if 'text' in message.keys():
        message_instance.text = message.get('text')
    elif channel.is_media_allowed:

        if 'photo' in message.keys():
            # get only original size, it always last
            file_id = message['photo'][-1].get('file_id')
            message_instance.url = tg_get_path_file(
                channel.telegram_token, file_id
            )
            download_to_file_field(url=message_instance.url,
                                   field=message_instance.image)
            # save caption of the image
            message_instance.text = {message.get('caption')}

        for type_file in ['document', 'audio', 'video', 'voice', 'sticker']:
            if type_file in message.keys():
                file_id = message[type_file].get('file_id')
                message_instance.url = tg_get_path_file(
                    channel.telegram_token, file_id
                )
                download_to_file_field(url=message_instance.url,
                                       field=message_instance.file)
                # save caption of the file
                message_instance.text = {message.get('caption')}

    location = message.get('location')
    if location and channel.is_geo_allowed:
        message_instance.location = location

    if is_help_message:
        message_instance.is_help_message = True

    message_instance.save()


def tg_get_path_file(token: str, file_id: str) -> str:
    """
    return url-path for download file from telegram
    """
    tg_bot = TeleBot(token)
    file_info = tg_bot.get_file(file_id)
    return f"https://api.telegram.org/file/bot{token}/{file_info.file_path}"


def download_to_file_field(url, field) -> None:
    """
    download file on server
    """
    try:
        name, _ = urlretrieve(url)
        field.save(basename(urlsplit(url).path), File(open(name, 'rb')))
    finally:
        urlcleanup()


def send_message_with_media(data: dict, action: Action) -> Message:
    """
        Sending message by type media
    """
    action_type: str = action.action_type
    if action_type == "picture" and action.picture:
        response = send_media(
            **data,
            file_path=action.picture.path,
            media_type='photo',
        )
    elif action_type == "url" and action.url:
        response = send_message(
            **data,
            text=action.url,
        )
    elif action_type == "video" and action.video:
        response = send_media(
            **data,
            file_path=action.video.path,
            media_type='video',
        )
    elif action_type == "file" and action.file:
        response = send_media(
            **data,
            file_path=action.file.path,
            media_type='document'
        )
    elif all([action_type == "location",
              action.location_latitude,
              action.location_longitude]):
        response = send_location(
            **data,
            lon=action.location_longitude,
            lat=action.location_latitude,
        )
    elif action_type == "sticker" and action.sticker_id:
        response = send_sticker(
            sticker_id=action.sticker_id,
            **data,
        )
    return response


def get_action(in_data: dict, channel: Channel) -> Action:
    """
    Find action in response to a message
    """
    user_text: str = in_data["message"].get("text")
    if user_text:
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
