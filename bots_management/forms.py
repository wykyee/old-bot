from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from bots_management.models import Channel, Bot
from bots_management.services import (
    get_all_related_bots, get_all_bots
)
from keyboards.models import Action


class ChannelForm(forms.ModelForm):
    name = forms.CharField(
        label='Назва каналу',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    slug = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    is_media_allowed = forms.CheckboxInput(attrs={
        'class': 'form-control modal__field',
        'id': 'i_allowUserMedia'

    })
    is_geo_allowed = forms.CheckboxInput(attrs={
        'class': 'form-control modal__field',
        'id': "i_allowUserGeolocation"
    })
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control modal__field',
            'id': 'i_description'
        })
    )
    welcome_action = forms.ModelChoiceField(
        label='Привітальне повідомлення', required=False,
        queryset=Action.objects.none(),
        widget=forms.Select(
            attrs={'class': "form-control js-example-basic-single"}
        )
    )


class SuperuserChannelForm(ChannelForm):
    """
    Only superuser can allow to mail without admin confirmation
    and add new moderators.
    """
    moderators = forms.ModelMultipleChoiceField(
        label='Модератори', queryset=get_user_model().objects.all(),
        required=False,
        widget=forms.SelectMultiple(
            attrs={'class': "form-control js-example-basic-multiple"}
        )
    )

    class Meta:
        model = Channel
        fields = (
            "name", "slug", "moderators", "description",
            "is_geo_allowed", "is_media_allowed",
            "is_mailing_allowed", "welcome_action"
        )


class ModeratorChannelForm(ChannelForm):
    class Meta:
        model = Channel
        fields = ("name", "slug", "description",
                  "is_geo_allowed", "is_media_allowed", "welcome_action")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        """
        Automatically saves user, who's created a channel as a moder.
        """
        channel = super().save(commit=False)
        if commit:
            channel.save()
        channel.moderators.add(self.user)
        return channel


class BotForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.channel = kwargs.pop("channel", None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        """
        Automatically saves channel from init as parent channel.
        """
        bot = super().save(commit=False)
        bot.channel = self.channel
        if commit:
            bot.save()

        return bot


class BotAddForm(BotForm):
    messenger = forms.ChoiceField(
        label='Месенджер', choices=Bot.messengers,
        widget=forms.Select(
            attrs={'class': "form-control js-example-basic-single"}
        )
    )

    class Meta:
        model = Bot
        fields = ("messenger", "token", "description",)
        widgets = {
            "token": forms.TextInput(attrs={'class': 'form-control'}),
            "description": forms.Textarea(attrs={'class': 'form-control'})
        }

    def clean_token(self):
        token = self.cleaned_data.get("token")
        bots = get_all_bots()

        if token in (bot.token for bot in bots):
            raise ValidationError("Такий токен вже існує")

        return token

    def clean_messenger(self):
        messenger = self.cleaned_data.get("messenger")
        bots = get_all_related_bots(self.channel)

        if messenger in (bot.messenger for bot in bots):
            raise ValidationError("Такий месенджер вже є на цьому каналі")

        return messenger


class BotUpdateForm(BotForm):
    class Meta:
        model = Bot
        fields = ("token", "description",)
        widgets = {
            "token": forms.TextInput(attrs={'class': 'form-control'}),
            "description": forms.Textarea(attrs={'class': 'form-control'})
        }


class ChannelFrontForm(forms.ModelForm):
    name = forms.CharField(
        label='Назва каналу',
        widget=forms.TextInput(attrs={'class': 'form-control modal__field',
                                      'id': 'i_title'})
    )
    slug = forms.CharField(
        label='URL',
        widget=forms.TextInput(attrs={'class': 'form-control modal__field',
                                      'id': 'i_url'})
    )
    is_media_allowed = forms.CheckboxInput(
        attrs={'class': 'form-control modal__field',
               'id': "i_allowUserMedia"})
    is_geo_allowed = forms.CheckboxInput(
        attrs={'class': 'form-control modal__field',
               'id': "i_allowUserGeolocation"})
    description = forms.CharField(
        label='Опис', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control modal__field',
                                      'id': 'i_description'})
    )
    moderators = forms.ModelMultipleChoiceField(
        label='Модератори', queryset=get_user_model().objects.all(),
        required=False, widget=forms.SelectMultiple(
            attrs={'class': "select2-search",
                   'id': "i_moderators"}
        )
    )

    class Meta:
        model = Channel
        fields = ('name', 'slug', 'moderators', 'is_media_allowed',
                  'is_geo_allowed', 'description',)
