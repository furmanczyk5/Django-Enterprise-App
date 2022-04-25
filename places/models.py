from django.db import models
from content.models import BaseContent, Content, Tag, Publishable


PLACE_TYPES = (
    ("CENSUS_CITY","US City (or other incorporated place or census designated place)"),
    ("COUNTY", "US County"),
    ("COUNTY_SUBDIVISION", "US County Subdivsion"),
    ("STATE", "US State"),
    ("CENSUS_REGION", "US Census Region"),
)

LSAD = (
    ("21", "Borough"),
    ("25", "City"),
    ("37", "Municipality"),
    ("43", "Town"),
    ("47", "Village"),
    ("53", "City and borough"),
    ("55", "Comunidad"),
    ("57", "CDP"),
    ("62", "Zona urbana"),
    ("CN", "Corporation (incorporated place)"),
    ("MG", "Metropolitan government"),
    ("UC", "Urban county"),
    ("UG", "Unified government"),
    ("00", "(other LSAD)"),
)

CENSUS_REGION_STATE = (
    ("MOUNTAIN", ["AZ", "CO", "ID", "MT", "NM", "NV", "UT", "WY"] ),
    ("MIDDLE_ATLANTIC", ["NJ", "NY", "PA"] ),
    ("NEW_ENGLAND", ["CT", "ME", "MA", "NH", "RI", "VT"] ),
    ("EAST_SOUTH_CENTRAL", ["AL", "KY", "MS", "TN"] ),
    ("WEST_SOUTH_CENTRAL", ["AR", "LA", "OK", "TX"] ),
    ("SOUTH_ATLANTIC", ["DC", "DE", "FL", "GA", "MD", "NC", "SC", "VA", "WV"] ),
    ("EAST_NORTH_CENTRAL", ["IL", "IN", "MI", "OH", "WI"] ),
    ("WEST_NORTH_CENTRAL", ["IA", "KS", "MN", "MO", "ND", "NE", "SD"] ),
    ("PACIFIC", ["AK", "CA", "HI", "OR", "WA"] )
)


# -------------------------------------------------------------------------------
# TAXO PLACE RELATED STUFF:

class ContentPlace(Publishable):
    content = models.ForeignKey(Content, related_name="contentplace", on_delete=models.CASCADE)
    place = models.ForeignKey('Place', related_name="contentplace", on_delete=models.CASCADE)
    # will these even be needed?
    tag_parent_state = models.BooleanField(default=True)
    # add tag for metro regions here...
    tag_parent_region = models.BooleanField(default=True)
    tag_place_data = models.BooleanField(default=True)
    sort_number = models.IntegerField(null=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)


class Place(BaseContent):

    #note... place name should be specified by the title (inherited from BaseContent)

    place_type = models.CharField(max_length=50, choices=PLACE_TYPES, default="CENSUS_CITY")
    lsad = models.CharField(max_length=5, choices=LSAD, default="00") # MAYBE TO DO... make this optional?
    region = models.ForeignKey(
        Tag,
        null=True,
        blank=True,
        related_name="place",
        limit_choices_to={"tag_type__code":"CENSUS_REGION"},
        on_delete=models.SET_NULL
    )
    country = models.CharField(max_length=50, null=True, blank=True)
    state_code = models.CharField(max_length=15, null=True, blank=True) # the code for the state
    state_name = models.CharField(max_length=200, null=True, blank=True)

    place_descriptor_name = models.CharField(max_length=200, null=True, blank=True)
    census_geo_id = models.CharField(max_length=50, null=True, blank=True)
    # MAYBE TO DO... also include field for ANSI code?
    un_region_id = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        state_code = self.state_code or ""
        place_descriptor_name = self.place_descriptor_name or ""
        if self.place_type=="CENSUS_CITY":
            return "%s, %s" % (self.title, state_code)
        elif self.place_type in ("COUNTY", "COUNTY_SUBDIVISION"):
            return "%s %s, %s" % (self.title, place_descriptor_name,  state_code)
        else:
            return str(self.title)


class PlaceData(models.Model):
    place = models.ForeignKey('Place', on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)
    year = models.IntegerField()
    source_name = models.CharField(max_length=200, null=True, blank=True)
    population = models.IntegerField(null=True, blank=True)
    housing_units = models.IntegerField(null=True, blank=True)

    # TO DO: remove density (use method below instead)
    density = models.IntegerField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    land_sq_miles = models.FloatField(null=True, blank=True)
    water_sq_miles = models.FloatField(null=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    def get_density(self):
        try:
            return round( self.population / self.land_sq_miles, 2)
        except:
            return None



