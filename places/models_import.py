import csv
from .models import ContentPlace, Place, PlaceData

# NOTE: functions to import places are included here (as opposed to a file in the generic _data_tools foler)
# because we expect to need to continue importing place data regularly (as opposed to a 1-off migration of data).


def places_from_gaz(filepath="./places/temp/data_2010/Gaz_places_national.txt", place_type="CENSUS_CITY", census_year=2010):
    with open(filepath, encoding="ISO-8859-1") as f:
        reader = csv.reader(f, delimiter="\t")
        d = list(reader)
    for p in d[1:]:
        place, created = Place.objects.get_or_create(place_type=place_type, census_geo_id=p[1].strip())
        try:
            place.title = p[3].strip().rsplit(' ', 1)[0]
            place.place_descriptor_name = p[3].strip().rsplit(' ', 1)[1]
        except:
            place.title=p[3].strip()
        if place_type=="CENSUS_CITY":
            place.lsad = p[4].strip()
        place.state_code = p[0].strip()
        place.save()
        print( ("CREATED: " if created else "UPDATED: ") + str(place) )

        pd, created = PlaceData.objects.get_or_create(place=place, year=census_year)
        pd.source_name = "US Census"
        if place_type=="COUNTY":
            try:
                pd.population = int(p[4].strip())
            except:
                pass
            try:
                pd.housing_units = int(p[5].strip())
            except:
                pass
            try:
                pd.land_sq_miles = float(p[8].strip())
            except:
                pass
            try:
                pd.water_sq_miles = float(p[9].strip())
            except:
                pass
            try:
                pd.latitude = float(p[10].strip())
            except:
                pass
            try:
                pd.longitude = float(p[11].strip())
            except:
                pass
        elif place_type=="COUNTY_SUBDIVISION":
            try:
                pd.population = int(p[5].strip())
            except:
                pass
            try:
                pd.housing_units = int(p[6].strip())
            except:
                pass
            try:
                pd.land_sq_miles = float(p[9].strip())
            except:
                pass
            try:
                pd.water_sq_miles = float(p[10].strip())
            except:
                pass
            try:
                pd.latitude = float(p[11].strip())
            except:
                pass
            try:
                pd.longitude = float(p[12].strip())
            except:
                pass
        elif place_type=="CENSUS_CITY":
            try:
                pd.population = int(p[6].strip())
            except:
                pass
            try:
                pd.housing_units = int(p[7].strip())
            except:
                pass
            try:
                pd.land_sq_miles = float(p[10].strip())
            except:
                pass
            try:
                pd.water_sq_miles = float(p[11].strip())
            except:
                pass
            try:
                pd.latitude = float(p[12].strip())
            except:
                pass
            try:
                pd.longitude = float(p[13].strip())
            except:
                pass
        # print(place_type)
        # print(pd.population)
        # print(pd.housing_units)
        # print(pd.land_sq_miles)
        # print(pd.water_sq_miles)
        pd.save()

def county_subdivisions_from_gaz(filepath="./places/temp/data_2010/Gaz_cousubs_national.txt", place_type="COUNTY_SUBDIVISION", census_year=2010):
    places_from_gaz(filepath=filepath, place_type=place_type, census_year=census_year)

def counties_from_gaz(filepath="./places/temp/data_2010/Gaz_counties_national.txt", place_type="COUNTY", census_year=2010):
    places_from_gaz(filepath=filepath, place_type=place_type, census_year=census_year)


def print_lsad(filepath):
    """
    Just a tool to show the possible LSAD values from a places data file
    """
    lsad_set = set()
    with open(filepath, encoding="ISO-8859-1") as f:
        reader = csv.reader(f, delimiter="\t")
        d = list(reader)
    for item in d[1:]:
        lsad_set.add(item[4])

    for lsad in lsad_set:
        print(lsad)
