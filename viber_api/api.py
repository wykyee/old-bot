import logging
import json
import requests

logger = logging.getLogger(__name__)


def get_bot_info(token: str) -> dict:
    """
        Get information about token viber bot
    """
    response = requests.get(
        "https://chatapi.viber.com/pa/get_account_info",
        headers={
            "X-Viber-Auth-Token": token,
            "Content-Type": "application/json"
        },
    )
    return response.json()


def send_message(data: dict, token: str, broadcast: bool = False) -> None:
    """
    Send message to Viber's subscribers
    """
    url = "https://chatapi.viber.com/pa/send_message"
    if broadcast:
        url = "https://chatapi.viber.com/pa/broadcast_message"
    # logger.error(data)
    r = requests.post(
        url,
        json.dumps(data),
        headers={
            "X-Viber-Auth-Token": token,
            "Content-Type": "application/json",
        },
    )
    if r.json().get('status'):
        logger.warning(r.text)


def set_webhook_ajax(slug: str, host: str, token: str) -> dict:
    """
    Set viber webhook for certain channel with ajax.
    """
    headers = {
        "X-Viber-Auth-Token": token,
        "Content-Type": "application/json"
    }
    webhook_url = f"https://{host}/viber_prod/{slug}/"
    data = dict(url=webhook_url, event_types=[
        "subscribed",
        "unsubscribed",
        "conversation_started",
        "delivered",
        "failed",
        "message",
        "seen",
    ])
    url = "https://chatapi.viber.com/pa/set_webhook"
    response = requests.post(url, json.dumps(data), headers=headers)
    logger.warning(
        f"""Set viber-webhook with ajax {webhook_url}.
        token {token}. Answer: {response.text}"""
    )
    return response.json()


def remove_webhook_ajax(token: str) -> dict:
    """
        Unset viber webhook for certain channel with ajax.
    """
    headers = {
        "X-Viber-Auth-Token": token,
        "Content-Type": "application/json"
    }
    url = "https://chatapi.viber.com/pa/set_webhook"
    data = dict(url="")
    response = requests.post(url, json.dumps(data), headers=headers)
    logger.warning(
        f"""Unset viber-webhook token {token}.
        Answer: {response.text}"""
    )
    return response.json()
