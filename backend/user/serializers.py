from multiprocessing import context
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

from .models import CustomUser
from recipes.models import Follow


class CustomUserSerializer(serializers.ModelSerializer):
    """ Сериализатор для модели Юзера. """
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed',)

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(following=obj).exists()


class UsersCreateSerializer(UserCreateSerializer):
    """ Сериализатор для создания Юзера. """

    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name', 'password', )
