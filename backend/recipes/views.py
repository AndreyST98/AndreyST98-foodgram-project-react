from django.db.models import Sum
from django.http.response import HttpResponse
from djoser.views import UserViewSet
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly,)
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from recipes.filters import IngredientsFilter, RecipeFilter
from user.serializers import CustomUserSerializer
from user.models import CustomUser
from .models import (Favorite, Follow, Ingredient, IngredientAmount, Recipe,
                     ShopList, Tag)
from .serializers import (FollowCreateSerializer, FollowSerializer,
                          IngredientSerializer, RecipesCreateSerializer, RecipesSerializer,
                          TagSerializer, UserFollowSerializer)
from .utils import adding_obj_view, delete_obj_view


class CustomUserViewSet(UserViewSet):
    """ Вьюсет для модели пользователя с дополнительным операциями
        через GET запросы. """

    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = PageNumberPagination
    permission_classes = (IsAuthenticated,)

    @action(detail=True, methods=['post'], url_path='subscribe')
    def user_subscribe_add(self, request, id):
        user = request.user
        following = get_object_or_404(CustomUser, pk=id)
        serializer = FollowCreateSerializer(
            data={'user': user.id, 'following': id},
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        follow = get_object_or_404(Follow, user=user, following=following)
        serializer = UserFollowSerializer(follow.following, context={'request': request})
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

    @action(methods=['GET'], url_path='subscriptions', detail=False)
    def subscriptions(self, request):
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
    pagination_class = None
    search_fields = ['name']


class IngredientViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    filter_backends = [DjangoFilterBackend, ]
    filterset_class = IngredientsFilter
    pagination_class = None


class RecipesViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = RecipesSerializer
    queryset = Recipe.objects.all().order_by('-id')
    filter_backends = [DjangoFilterBackend, ]
    filterset_class = RecipeFilter

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
        """ Метод добавления рецепта в избранное. """

        user = request.user
        model = Favorite
        return adding_obj_view(model=model, user=user, pk=pk)

    @recipe_id_favorite.mapping.delete
    def recipe_id_favorite_del(self, request, pk):
        """ Метод удаления рецепта в избранное. """

        user = request.user
        model = Favorite
        return delete_obj_view(model=model, user=user, pk=pk)

    @action(detail=True, url_path='shopping_cart', methods=['POST', 'GET'],
            permission_classes=[IsAuthenticated])
    def recipe_cart(self, request, pk):
        """ Метод добавления рецепта в список покупок. """

        user = request.user
        model = ShopList
        return adding_obj_view(model=model, user=user, pk=pk)

    @recipe_cart.mapping.delete
    def recipe_cart_del(self, request, pk):
        """ Метод удаления рецепта из списка покупок. """

        user = request.user
        model = ShopList
        return delete_obj_view(model=model, user=user, pk=pk)

    @action(detail=False,
            url_path='download_shopping_cart',
            methods=['GET', 'POST'],
            permission_classes=[permissions.IsAuthenticated])
    def download_cart_recipe(self, request):
        """ Метод скачивания списка продуктов. """
        ingredients_list = IngredientAmount.objects.filter(
            recipe__cart_recipe__user=request.user
        ).values('ingredient__name', 'ingredient__measurement_unit').order_by(
            'ingredient__name').annotate(tolal_sum=Sum('amount'))
        response = HttpResponse(ingredients_list, 'Content-Type: text/plain')
        response['Content-Disposition'] = 'attachment; filename=cart_recipe'
        return response
