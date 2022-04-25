"""
iMIS has a 25 character limit on country names, leading to some...interesting abbreviations
in its Country_Names table.

Since coming up with names like "Congo, The Dem Rep Of The" was apparently easier than lifting
a character limit, I am proceeding under the assumption that we are stuck with this for the
foreseeable future and decided to make this mapping of those long country names to the country
names in the geonames dataset that our cities_light dependency uses that we in turn use
to populate form options from :meth:`ui.utils`
 in :class:`content.forms.StateCountryModelFormMixin`


OUTSTANDING ISSUES REMAINING:
- iMIS still only has "Serbia and Montenegro" despite the fact that they've been separate countries since 2006
- iMIS missing South Sudan

https://americanplanning.atlassian.net/browse/DEV-5433
"""

# geonames country key: imis country value
GEONAMES_IMIS_COUNTRY_MAPPING = {
    "British Indian Ocean Territory": "British Indian Ocean Terr",
    "Cocos Islands": "Cocos (Keeling) Islands",
    "Democratic Republic of the Congo": "Congo, The Dem Rep Of The",
    "French Southern Territories": "French Southern Terr",
    "Heard Island and McDonald Islands": "Heard Is and McDonald Is",
    "Kosovo": "Kosovo, Republic of",
    "Republic of the Congo": "Congo (Brazzaville)",
    "South Georgia and the South Sandwich Islands": "South Georgia and the SSI",
    "U.S. Virgin Islands": "Virgin Islands, US",
    "United States Minor Outlying Islands": "US Minor Outlying Islands",
    "Vatican": "Holy See (Vatican City)"
}
