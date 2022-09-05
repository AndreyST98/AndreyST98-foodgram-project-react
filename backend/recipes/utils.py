from django.http.response import HttpResponse
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT

from .models import Recipe
from .serializers import RecipeFollowSerializer


def adding_obj_view(model, user, pk):
    recipe = get_object_or_404(Recipe, id=pk)
    if model.objects.filter(user=user, recipe=recipe).exists():
        return Response('Рецепт добавлен в список',
                        status=status.HTTP_400_BAD_REQUEST)
    add_cart = model.objects.create(user=user, recipe=recipe)
    serializer = RecipeFollowSerializer(add_cart.recipe)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def delete_obj_view(model, user, pk):
    recipe = get_object_or_404(Recipe, id=pk)
    if not model.objects.filter(user=user, recipe=recipe).exists():
        return Response('Рецепт отсутствует',
                        status=status.HTTP_400_BAD_REQUEST)
    obj = model.objects.filter(user=user, recipe__id=pk)
    obj.delete()
    return Response(status=HTTP_204_NO_CONTENT)


def download_card(download_list, filename):
    response = HttpResponse(download_list, 'Content-Type: text/plain')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
