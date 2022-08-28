from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from user.models import CustomUser
from user.serializers import CustomUserSerializer

from .models import (Favorite, Follow, Ingredient, IngredientAmount, Recipes,
                     ShopList, Tag)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Тэг"""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ингридиенты"""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """ Сериализатор для модели Ингредиенты в рецептах. """

    id = serializers.IntegerField()
    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount',)

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit


class RecipesSerializer(serializers.ModelSerializer):
    """ Сериализатор для рецептов. """
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(many=True)
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipes
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        if self.context['request'].user.is_authenticated:
            current_user = self.context['request'].user
            return Favorite.objects.filter(user=current_user,
                                           recipes=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        if 'request' not in self.context:
            raise serializers.ValidationError('Invalid request')
        if self.context['request'].user.is_authenticated:
            current_user = self.context['request'].user
            return ShopList.objects.filter(customer=current_user,
                                           recipe=obj).exists()


class CreateIngredientRecipeSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField()

    class Meta:
        model = IngredientAmount
        fields = ('id', 'amount')


class RecipesCreateSerializer(serializers.ModelSerializer):
    """ Сериализатор для создания объекторв модели Рецепты,
        с методами создания и обновления. """
    author = CustomUserSerializer(read_only=True)
    ingredients = CreateIngredientRecipeSerializer(many=True)

    class Meta:
        model = Recipes
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def create(self, validated_data):
        request = self.context.get('request')
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipes.objects.create(author=request.user, **validated_data)
        for ingredient in ingredients:
            temp = IngredientAmount.objects.create(
                ingredient=Ingredient.objects.get(pk=ingredient['id']),
                amount=ingredient['amount'])
            recipe.ingredients.add(temp)
        for tag in tags:
            recipe.tags.add(tag)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        for ingredient in ingredients:
            temp = IngredientAmount.objects.create(
                ingredient=Ingredient.objects.get(
                    pk=ingredient['id']),
                amount=ingredient['amount'])
            instance.ingredients.add(temp)
        instance.tags.clear()
        for tag in tags:
            instance.tags.add(tag)
        return super().update(instance, validated_data)


class RecipeFollowSerializer(RecipesSerializer):
    """ Сериализатор модели Рецепты для отображения
        в подписках. """

    class Meta:
        model = Recipes
        fields = ('id', 'name', 'image', 'cooking_time')


class UserFollowSerializer(CustomUserSerializer):
    """ Сериализатор модели Пользователя, для отображения
        в подписках. """
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')
        model = CustomUser

    def get_recipes(self, obj):
        request = self.context['request']
        limit = request.GET.get('recipes_limit')
        queryset = Recipes.objects.filter(author=obj)
        if limit:
            queryset = queryset[:int(limit)]
            return RecipeFollowSerializer(queryset, many=True).data
        return RecipeFollowSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        recipes = Recipes.objects.filter(author=obj)
        return recipes.count()


class FollowSerializer(serializers.ModelSerializer):
    """ Сериализатор для подписок. """

    email = serializers.ReadOnlyField(source='following.email')
    id = serializers.ReadOnlyField(source='following.id')
    username = serializers.ReadOnlyField(source='following.email')
    first_name = serializers.ReadOnlyField(source='following.first_name')
    last_name = serializers.ReadOnlyField(source='following.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')
        model = Follow

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(
            user=obj.user, following=obj.following
        ).exists()

    def get_recipes(self, obj):
        request = self.context['request']
        limit = request.GET.get('recipes_limit')
        queryset = Recipes.objects.filter(author=obj.following)
        if limit:
            queryset = queryset[:int(limit)]
        return RecipeFollowSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return Recipes.objects.filter(author=obj.following).count()


class FollowCreateSerializer(serializers.ModelSerializer):
    """ Сериализатор создания объекта Подписки. """

    class Meta:
        fields = ('user', 'following')
        model = Follow
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=['user', 'following'],
                message=['Вы уже подписаны на этого пользователя']
            )
        ]

    def validate(self, data):
        user = data['user']
        current_follow = data['following']
        if user == current_follow:
            raise serializers.ValidationError(
                ['Нельзя подписаться на самого себя'])
        return data
