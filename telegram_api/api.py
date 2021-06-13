import json
import logging
from typing import Union

import requests

from django.conf import settings

from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, Message
from telebot.apihelper import ApiException

from moviepy.editor import VideoFileClip

from bots_management.models import Bot
from keyboards.models import IdFilesInMessenger
from subscribers.models import Subscriber


logger = logging.getLogger(__name__)


def get_webhook_info(token: str) -> dict:
    """
    Get information about tg webhook
    """
    res = requests.get(settings.TELEGRAM_BASE_URL % (token, "getWebhookInfo"))
    return res.json().get('result')


def get_bot_info(token: str) -> dict:
    """
        Get information about tg bot
    """
    res = requests.get(settings.TELEGRAM_BASE_URL % (token, "getMe"))
    return res.json().get('result')


def checking_send_message(function):
    """
    decorator for logging sending message in telegram
    """
    def send_message_with_check(*arg, **kwargs):
        try:
            return function(*arg, **kwargs)
        except ApiException as e:
            e = str(e)
            response = json.loads(
                e[e.index('{'):e.index('}')+1]
            ).get('description')
            if response == 'Forbidden: bot was blocked by the user':
                bot = Bot.objects.filter(token=kwargs.get('token')).first()
                subscriber = Subscriber.objects.filter(
                    user_id=kwargs.get('chat_id'),
                    messengers_bot=bot,
                )
                if subscriber.exists():
                    subscriber.update(is_active=False)
                    # TODO it's works, but don't save changes in db
                    logger.warning(
                        f"""User {subscriber} unsubscribed (is_active=False)"""
                    )
            logger.warning(
                f"""Send {function.__name__} to {kwargs.get('chat_id')} failed.
                token: {kwargs.get('token')}.
                Error: {e}"""
            )
        except Exception as e:
            logger.critical(
                f"""Send {function.__name__} to {kwargs.get('chat_id')} failed.
                token: {kwargs.get('token')}.
                Error: {e}"""
            )
    return send_message_with_check


@checking_send_message
def send_message(chat_id: int, text: str, token: str,
                 reply_markup: ReplyKeyboardMarkup = None,
                 **kwargs) -> Message:
    """Sends `sendMessage` API request to the telegramAPI.

    chat_id: Id of the chat.
    text: Text of the message.
    reply_markup: Instance of the `InlineKeyboardMarkup`.
    token: bot's token

    Returns: None.
    """
    response: Message = TeleBot(token).send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup
    )
    return response


@checking_send_message
def send_media(chat_id: int, token: str,
               action: object, media_type: str,
               file_path: str = None, file_id: str = None,
               **kwargs) -> Message:
    """Sends `sendPhoto` API request to the telegramAPI.

        chat_id: Id of the chat.
        token: telegram token.
        action: Action for checking saved id_document.
        media_type: type of media (photo, video, document)
        file_path: path to the file.
        file_id: id of the file

        Returns: Message.
    """
    if not file_id:
        file_id = check_file_id(action, file_path, token)
    if not file_id and not file_path:
        logger.error(f'file_id or file_path  '
                     f'must be provided {chat_id}/{token}')
        return
    if file_id:
        response = send_media_with_id(chat_id, token, media_type, file_id)
    else:
        response = send_media_without_id(
            chat_id, token, media_type, action, file_path
        )
    return response


def send_media_with_id(chat_id: int, token: str,
                       media_type: str, file_id: str = None, ) -> Message:
    """
    send media in telegram if we have file_id
    """
    if media_type == 'photo':
        response: Message = TeleBot(token).send_photo(
            chat_id=chat_id, photo=file_id
        )
    if media_type == 'video':
        response: Message = TeleBot(token).send_video(
            chat_id=chat_id, data=file_id
        )
    if media_type == 'document':
        response: Message = TeleBot(token).send_document(
            chat_id=chat_id, data=file_id
        )
    return response


def send_media_without_id(chat_id: int, token: str,
                          media_type: str, action: object,
                          file_path: str = None, ) -> Message:
    """
        send media in telegram if we have only file_path,
        ad save file id in database
    """
    if media_type == 'photo':
        with open(file_path, 'rb') as file:
            response: Message = TeleBot(token).send_photo(
                chat_id=chat_id, photo=file
            )
            file_id = response.json.get('photo')[-1].get('file_id')
    if media_type == 'video':
        with open(file_path, 'rb') as file:
            clip = VideoFileClip(file_path)
            response: Message = TeleBot(token).send_video(
                chat_id=chat_id, data=file, duration=clip.duration
            )
            file_id = response.json.get('video').get('file_id')
    if media_type == 'document':
        with open(file_path, 'rb') as file:
            response: Message = TeleBot(token).send_document(
                chat_id=chat_id, data=file
            )
            file_id = response.json.get('document').get('file_id')
    update_or_create_file_id(action, file_path, file_id, token)
    return response


@checking_send_message
def send_location(chat_id: int, token: str,
                  lat: int, lon: int, **kwargs) -> Message:
    """Sends `sendLocation` API request to the telegramAPI.

    chat_id: Id of the chat.
    lat: Latitude.
    lon: Longitude.
    token: bot's token

    Returns: None.
    """
    response: Message = TeleBot(token).send_location(
        chat_id=chat_id,
        longitude=lon,
        latitude=lat
    )
    return response


@checking_send_message
def send_sticker(chat_id: int, token: str,
                 sticker_id: str = None, **kwargs) -> Message:
    """Sends `sendSticker` API request to the telegramAPI.

    chat_id: Id of the chat.
    sticker_path: path to the sticker.
    sticker_id: id of the sticker
    token: bot's token

    Returns: None.
    """
    if sticker_id:
        sticker_id = sticker_id.split('//')
        if len(sticker_id) == 2:
            response = TeleBot(token).send_sticker(
                chat_id=chat_id, data=sticker_id[1]
            )
            return response


@checking_send_message
def delete_message(chat_id: Union[str, int], message_id: int,
                   token: str) -> bool:
    """
    Delete message using Telegram API
    :param chat_id: Id of a chat.
    :param message_id: Id of a message.
    :param token: Bot`s token
    """
    response = TeleBot(token).delete_message(chat_id=chat_id, message_id=message_id)
    return response


def set_webhook_ajax(slug: str, host: str, token: str) -> dict:
    """
    Sets telegram webhook for certain channel.
    """
    webhook = f"https://{host}/telegram_prod/{slug}/"
    url = f"https://api.telegram.org/bot{token}/setWebhook?url={webhook}"
    response = requests.get(url)
    logger.warning(
        f"""Set telegram-webhook with ajax {url}.
            token {token}. Answer: {response.text}"""
    )
    return response.json()


def unset_webhook_ajax(token: str) -> dict:
    """
    Sets telegram webhook for certain channel.
    """
    webhook = ""
    url = f"https://api.telegram.org/bot{token}/setWebhook?url={webhook}"
    response = requests.get(url)
    logger.warning(
        f"""Set telegram-webhook with ajax {url}.
            token {token}. Answer: {response.text}"""
    )
    return response.json()


def check_file_id(action: object,
                  file_path: str,
                  token: str) -> Union[str, None]:
    """
    Find file_id in database, if it was saved
    """
    info = IdFilesInMessenger.objects.filter(action=action, token_tg=token)
    if info.exists():
        info = info.first()
        if info.path_media_tg == file_path:
            return info.telegram_id


def update_or_create_file_id(action: object,
                             file_path: str = None,
                             file_id: str = None,
                             token: str = None) -> IdFilesInMessenger:
    """
        Save file_id in database
    """
    return IdFilesInMessenger.objects.update_or_create(
        action=action,
        token_tg=token,
        defaults={
            'action': action,
            'path_media_tg': file_path,
            'telegram_id': file_id,
            'token_tg': token,
        }
    )
