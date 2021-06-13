from typing import Union

from django.core.exceptions import ValidationError
from django.db.models import QuerySet, Q

from bots_management.models import Channel
from keyboards.models import Keyboard, Action, Button


def get_keyboards_related_to_channel(slug: str) -> QuerySet:
    return Keyboard.objects.filter(channel__slug=slug)


def get_keyboards_button_action_related_to_channel(slug: str) -> QuerySet:
    return Button.objects.select_related(
        "action", "keyboard"
    ).filter(keyboard__channel__slug=slug).prefetch_related(
        "action__keyboard_to_represent"
    )


def get_keyboard_by_pk_related_to_channel(pk: int,
                                          slug: str) -> Union[Keyboard, None]:
    return Keyboard.objects.filter(Q(pk=pk) & Q(channel__slug=slug)).first()


def get_keyboard_by_pk(pk: int) -> Union[Keyboard, None]:
    return Keyboard.objects.filter(pk=pk).first()


def get_actions_related_to_channel(slug: str) -> QuerySet:
    return Action.objects.prefetch_related(
        "keyboard_to_represent", "keyboard_to_represent__channel"
    ).filter(keyboard_to_represent__channel__slug=slug).order_by(
        "keyboard_to_represent"
    )


def get_actions_related_to_channel_by_obj(channel: object) -> QuerySet:
    return Action.objects.select_related(
        "keyboard_to_represent", "keyboard_to_represent__channel"
    ).filter(keyboard_to_represent__channel=channel)


def get_action_by_pk(pk: int) -> Union[Action, None]:
    return Action.objects.filter(pk=pk).first()


def get_home_action(slug: str) -> Union[Action, None]:
    """
    slug: slug of related channel.
    """
    # TODO mb another?
    home_action = Channel.objects.get(slug=slug).welcome_action
    if home_action:
        return home_action
    try:
        action = Action.objects.filter(
            keyboard_to_represent__channel__slug=slug
        ).first()
        return action
    except Action.DoesNotExist:
        raise ValidationError("Має бути хоча б якась подія")


def get_emergency_action(channel_slug: str) -> Union[Action, None]:
    """
    channel_slug: slug of related channel.

    return: action for emergency of certain channel.
    """
    return Action.objects.filter(
        Q(name="emergency_action") &
        Q(keyboard_to_represent__channel__slug=channel_slug)
    ).first()


def get_button_and_joined_action(text: str, channel_slug: str) -> QuerySet:
    """
    text: text of the button.
    channel_slug: slug of related channel.
    """

    return Button.objects.select_related("action").filter(
        Q(text=text) & Q(keyboard__channel__slug=channel_slug)
    )


def get_action_by_name(text: str, channel_slug: str) -> QuerySet:
    """
    text: user text for name action.
    channel_slug: slug of related channel.
    """
    return Action.objects.select_related("keyboard_to_represent").filter(
        Q(name=text) & Q(keyboard_to_represent__channel__slug=channel_slug)
    )


def get_buttons_related_to_keyboard(keyboard: Keyboard) -> QuerySet:
    return Button.objects.filter(keyboard=keyboard)
