from django_filters import rest_framework as django_filters

from recipes.models import Ingredient


class IngredientsFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name', )
