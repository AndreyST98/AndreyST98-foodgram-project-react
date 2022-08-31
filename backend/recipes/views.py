from djoser.views import UserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from user.models import CustomUser
from user.serializers import CustomUserSerializer

from .models import Favorite, Follow, Ingredient, Recipe, ShopList, Tag
from .serializers import (FollowCreateSerializer, FollowSerializer,
                          IngredientSerializer, RecipeFollowSerializer,
                          RecipesCreateSerializer, RecipesSerializer,
                          TagSerializer, UserFollowSerializer)


class CustomUserViewSet(UserViewSet):
    """ Вьюсет для модели пользователя с дополнительным операциями
        через GET запросы. """

    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = PageNumberPagination

    def get_permissions(self):
        if self.action == 'me':
            return (IsAuthenticated(),)
        return super().get_permissions()

    @action(detail=True, url_path='subscribe')
    def user_subscribe_add(self, request, id):
        user = request.user
        following = get_object_or_404(CustomUser, pk=id)
        serializer = FollowCreateSerializer(
            data={'user': user.id, 'following': id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        follow = get_object_or_404(Follow, user=user, following=following)
        serializer = UserFollowSerializer(follow.following,
                                          context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @user_subscribe_add.mapping.delete
    def user_subscribe_del(self, request, id):
        user = request.user
        following = get_object_or_404(CustomUser, pk=id)
        if not Follow.objects.filter(user=user,
                                     following=following).exists():
            return Response(['Вы не подписаны на этого пользователя'],
                            status=status.HTTP_400_BAD_REQUEST)
        follow = Follow.objects.get(user=user, following=following)
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=False, url_path='subscriptions',
            permission_classes=[IsAuthenticated])
    def user_subscriptions(self, request):
        user = request.user
        queryset = Follow.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class IngredientViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class RecipesViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = RecipesSerializer
    queryset = Recipe.objects.all().order_by('-id')
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PUT', 'PATCH'):
            return RecipesCreateSerializer
        return RecipesSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    @action(detail=True, url_path='favorite', methods=['POST', 'GET'],
            permission_classes=[IsAuthenticated])
    def recipe_id_favorite(self, request, pk):
        """
        Метод добавления рецепта в избранное
        с обработкой исключения .
        """
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            return Response('Рецепт уже добавлен в избранное',
                            status=status.HTTP_400_BAD_REQUEST)
        favorite = Favorite.objects.create(user=user, recipe=recipe)
        serializer = RecipeFollowSerializer(favorite.recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @recipe_id_favorite.mapping.delete
    def recipe_id_favorite_del(self, request, pk):
        """
        Метод удаления рецепта в избранное
        с обработкой исключения .
        """
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if not Favorite.objects.filter(user=user, recipe=recipe).exists():
            return Response('Рецепт отсутствует в избранном',
                            status=status.HTTP_400_BAD_REQUEST)
        favorite = Favorite.objects.get(user=user, recipes=recipe)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, url_path='shopping_cart', methods=['POST', 'GET'],
            permission_classes=[IsAuthenticated])
    def recipe_cart(self, request, pk):
        """
        Метод добавления рецепта в список покупок
        с обработкой исключения .
        """
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if ShopList.objects.filter(customer=user, recipe=recipe).exists():
            return Response('Рецепт добавлен в список',
                            status=status.HTTP_400_BAD_REQUEST)
        add_cart = ShopList.objects.create(customer=user, recipe=recipe)
        serializer = RecipeFollowSerializer(add_cart.recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @recipe_cart.mapping.delete
    def recipe_cart_del(self, request, pk):
        """
        Метод удаления рецепта в список покупок
        с обработкой исключения .
        """
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if not ShopList.objects.filter(user=user, recipe=recipe).exists():
            return Response('Рецепт отсутствует в списоке покупок',
                            status=status.HTTP_400_BAD_REQUEST)
        favorite = ShopList.objects.get(user=user, recipe=recipe)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
