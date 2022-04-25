from django.contrib import admin

from content.admin import BaseContentAdmin
from .models import ContentPlace, Place, PlaceData


class PlaceDataInline(admin.TabularInline):
    model = PlaceData
    extra = 0
    classes = ("grp-collapse grp-closed",)
    fields = ("priority", "year", "source_name", "population", "housing_units", "get_density", "land_sq_miles", "water_sq_miles", "latitude", "longitude")
    readonly_fields = ("get_density",)    

    def get_density(self, obj):
        # print( round(obj.get_density(), 2) )
        return ( obj.get_density() )
    get_density.short_description = "Density (population per sq mile)"

    # form = ContentTagTypeAdminForm

    # filter_horizontal = ('tags',)
    # readonly_fields = []

    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     """
    #     to remove the option to add search_topics and taxo_mastertopics through this Inline
    #     """
    #     if db_field.name == "tag_type":
    #         kwargs["queryset"] = TagType.objects.exclude(code__in=["SEARCH_TOPIC","TAXO_MASTERTOPIC", "JURISDICTION", "COMMUNITY_TYPE", "FORMAT"])
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # def get_queryset(self, request):
    #     return super().get_queryset(request).exclude(tag_type__code__in=["SEARCH_TOPIC","TAXO_MASTERTOPIC", "JURISDICTION", "COMMUNITY_TYPE", "FORMAT"])


class PlaceAdmin(BaseContentAdmin):
# class ConsultantAdmin(ContactAdmin):
    # readonly_fields=['get_imis_company', 'get_branch_offices']
    list_display = ("title", "state_code", "place_descriptor_name", "census_geo_id", "lsad", "place_type")
    search_fields = ("title", "census_geo_id")
    list_filter = ("place_type", "state_code", "place_descriptor_name")

    fieldsets = BaseContentAdmin.fieldsets[:]
    fieldsets.insert(1, ("Place Information", {
        "classes": ("grp-collapse grp-open",),
        "fields": (
            "place_type",
            ("region","state_code"),
            "place_descriptor_name",
            ("census_geo_id", "un_region_id"))
    }))

    inlines=[PlaceDataInline]


class ContentPlaceInline(admin.TabularInline):
    model = ContentPlace
    raw_id_fields=["place"]
    autocomplete_lookup_fields = {'fk': ["place"]}
    extra = 1
    fields = ("place", "tag_parent_state", "tag_parent_region",
              "tag_place_data", "sort_number")


class ContentPlaceAdmin(admin.ModelAdmin):
    raw_id_fields = ["content", "place"]
    autocomplete_lookup_fields = {'fk': ["content", "place"]}
    fields = ("content", "place", "tag_parent_state", "tag_parent_region",
              "tag_place_data", "sort_number")


admin.site.register(Place, PlaceAdmin)
admin.site.register(ContentPlace, ContentPlaceAdmin)
