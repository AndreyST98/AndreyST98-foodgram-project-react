from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from user.models import CustomUser
from user.serializers import CustomUserSerializer
from recipes.models import (Favorite, Follow, Ingredient, IngredientAmount, Recipe,
                            ShopList, Tag)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Тэг"""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ингредиенты"""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """ Сериализатор для модели Ингредиенты в рецептах. """

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class RecipesSerializer(serializers.ModelSerializer):
    """ Сериализатор для рецептов. """
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        required=True,
        source='ingredients_in_recipe')
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        if self.context['request'].user.is_authenticated:
            current_user = self.context['request'].user
            return Favorite.objects.filter(user=current_user,
                                           recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        if self.context['request'].user.is_authenticated:
            current_user = self.context['request'].user
            return ShopList.objects.filter(user=current_user,
                                           recipe=obj).exists()

    def validate(self, data):
        if 'request' not in self.context:
            raise serializers.ValidationError('Invalid request')
        return data


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
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time'
        )

    def validate(self, data):
        ingredients = data['ingredients']
        ingredient_list = []
        for items in ingredients:
            ingredient = get_object_or_404(
                IngredientAmount, id=items['id'])
            if ingredient in ingredient_list:
                raise serializers.ValidationError(
                    'Ингредиенты должны быть уникальными!')
            ingredient_list.append(ingredient)
        tags = data['tags']
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise serializers.ValidationError(
                    'Тэги должны быть уникальными!'
                )
            tags_list.append(tag)
        return data

    def create_ingredients(self, ingredients, recipe):
        create_ingredient = [
            IngredientAmount(
                recipe=recipe,
                ingredient=Ingredient.objects.get(pk=ingredient["id"]),
                amount=ingredient['amount']
            )
            for ingredient in ingredients]
        IngredientAmount.objects.bulk_create(create_ingredient)

    def create(self, validated_data):
        request = self.context.get('request')
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.tags.add(*tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)
        if 'tags' in validated_data:
            instance.tags.set(validated_data.pop('tags'))
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipesSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }).data


class RecipeFollowSerializer(RecipesSerializer):
    """ Сериализатор модели Рецепты для отображения
        в подписках. """

    class Meta:
        model = Recipe
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

    def to_representation(self, instance):
        authors = FollowSerializer(instance.following, context={'request': self.context.get('request')})
        return authors.data


class FollowSerializer(serializers.ModelSerializer):
    """ Сериализатор для подписок. """
    
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )
        read_only_fields = fields

    def get_is_subscribed(self, data):
        request = self.context.get('request')
        user = self.context['request'].user
        if not user:
            return False
        return data.follower.filter(following=request.user).exists()

    def get_recipes(self, data):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = (data.recipes.all()[:int(limit)] if limit else
                   data.recipes.all())
        context = {'request': request}
        return RecipeFollowSerializer(
            recipes, many=True, context=context
        ).data

    def get_recipes_count(self, data):
        return data.recipes.count()


class FollowCreateSerializer(serializers.ModelSerializer):
    """ Сериализатор создания объекта Подписки. """

    user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
    )
    following = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
    )

    class Meta:
        model = Follow
        fields = ('user', 'following')

    def validate(self, data):
        user = self.context.get('request').user
        following_id = data['following'].id
        if Follow.objects.filter(
            user=user,
            following=following_id,
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны!'
            )
        if user.id == following_id:
            raise serializers.ValidationError(
                'Вы не можете подписаться на самого себя!!'
            )
        return data
