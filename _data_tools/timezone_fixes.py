import time, pytz, datetime

import urllib
import string
import csv

from uszipcode import ZipcodeSearchEngine
from tzwhere import tzwhere

import django
django.setup()
from django.utils import timezone

from events.models import Event
from cm.models import Claim, Log
from cm.models import Period as CMPeriod
from jobs.models import Job
from submissions.models import Category, Period, Review


# dict of state/timezone lookups:
ET = pytz.timezone('US/Eastern')
CT = pytz.timezone('US/Central')
MT = pytz.timezone('US/Mountain')
PT = pytz.timezone('US/Pacific')

# these are incomplete -- states don't all fit cleanly in these anyway
PACIFIC_GROUP = ['CA', 'NV', 'WA', 'OR']
MOUNTAIN_GROUP = ['NM', 'WY','UT', 'CO', 'MT', 'ID', 'ND', 'SD', 'NE', 'KS']
CENTRAL_GROUP = ['AL', 'AR', 'IL', 'IA', 'LA', 'MN', 'MO', 'MS', 'OK', 'WI', 'IN', 'KY', 'MI', 'TN', 'TX']
EASTERN_GROUP = ['CT', 'DE', 'GA', 'ME', 'MD', 'MA', 'NH', 'NJ', 'NY', 'NC', 'OH', 'PA', 'RI', 'SC', 'VT', 'VA', 'WV']


tz_lookup = {'SC':ET}

# Get the zip code for a US state/city

"""
for each capitalized city and state, goes to USPS site
and gets the first zipcode
"""

# conversion table from USPS for STATE -> 2 digit abbreviation
us_states = {
    "ALABAMA":"AL"
    ,"ALASKA":"AK"
    ,"AMERICAN SAMOA":"AS"
    ,"ARIZONA":"AZ"
    ,"ARKANSAS":"AR"
    ,"CALIFORNIA":"CA"
    ,"COLORADO":"CO"
    ,"CONNECTICUT":"CT"
    ,"DELAWARE":"DE"
    ,"DISTRICT OF COLUMBIA":"DC"
    ,"FEDERATED STATES OF MICRONESIA":"FM"
    ,"FLORIDA":"FL"
    ,"GEORGIA":"GA"
    ,"GUAM":"GU"
    ,"HAWAII":"HI"
    ,"IDAHO":"ID"
    ,"ILLINOIS":"IL"
    ,"INDIANA":"IN"
    ,"IOWA":"IA"
    ,"KANSAS":"KS"
    ,"KENTUCKY":"KY"
    ,"LOUISIANA":"LA"
    ,"MAINE":"ME"
    ,"MARSHALL ISLANDS":"MH"
    ,"MARYLAND":"MD"
    ,"MASSACHUSETTS":"MA"
    ,"MICHIGAN":"MI"
    ,"MINNESOTA":"MN"
    ,"MISSISSIPPI":"MS"
    ,"MISSOURI":"MO"
    ,"MONTANA":"MT"
    ,"NEBRASKA":"NE"
    ,"NEVADA":"NV"
    ,"NEW HAMPSHIRE":"NH"
    ,"NEW JERSEY":"NJ"
    ,"NEW MEXICO":"NM"
    ,"NEW YORK":"NY"
    ,"NORTH CAROLINA":"NC"
    ,"NORTH DAKOTA":"ND"
    ,"NORTHERN MARIANA ISLANDS":"MP"
    ,"OHIO":"OH"
    ,"OKLAHOMA":"OK"
    ,"OREGON":"OR"
    ,"PALAU":"PW"
    ,"PENNSYLVANIA":"PA"
    ,"PUERTO RICO":"PR"
    ,"RHODE ISLAND":"RI"
    ,"SOUTH CAROLINA":"SC"
    ,"SOUTH DAKOTA":"SD"
    ,"TENNESSEE":"TN"
    ,"TEXAS":"TX"
    ,"UTAH":"UT"
    ,"VERMONT":"VT"
    ,"VIRGIN ISLANDS":"VI"
    ,"VIRGINIA":"VA"
    ,"WASHINGTON":"WA"
    ,"WEST VIRGINIA":"WV"
    ,"WISCONSIN":"WI"
    ,"WYOMING":"WY"
}


# core function. Give it a city in caps and 2 letter statecode, returns first zipcode
# WOULD HAVE TO CUSTOMIZE THIS FOR CURRENT WEBSITE LOOKUP FORMAT
def getzipcode(city, stateco):
    '''gets the first zipcode'''
    params = urllib.urlencode({'ctystzip':city + ' ' + stateco})
    f = urllib.urlopen('https://tools.usps.com/go/ZipLookupAction_input',params)
    for line in f.readlines():
        if string.find(line, '<b>' + city + ' ' + stateco)>=0:
            s=string.find(line,'------<BR><BR>')
            s = s + len('------<BR><BR>')
            return string.strip(line[s:(s+6)])
    f.close()


if __name__ == '__main__' or __name__ == 'builtins':
    #test the function with some data
    # your data table - STATE, CITY and ZIPCODE (this will probably be null)
    us_cities = [
        ("ALABAMA","MONTGOMERY","36101")
        ,("ALABAMA","SELMA","36701")
        ,("ALASKA","ANCHORAGE","99501")
        ,("ARIZONA","PHOENIX","85001")
        ,("ARIZONA","TUSCON","")
        ,("ARIZONA","WICKENBERG","")
        ,("ARKANSAS","FAYETTEVILLE","")
        ,("ARKANSAS","LITTLE ROCK","")
        ,("CALIFORNIA","SAN FRANCISCO","")
        ,("COLORADO","BOULDER","")
        ,("COLORADO","MOSCA","")
        ,("CONNECTICUT","ESSEX","")
        ,("CONNECTICUT","MIDDLETOWN","")
        ,("CONNECTICUT","NEW MILFORD","")
        ,("CONNECTICUT","WESTON","")
        ,("FLORIDA","ALTAMONTE SPRINGS","")
        ,("FLORIDA","APALACHICOLA OR OTHER","")
        ,("FLORIDA","BRISTOL","")
        ,("FLORIDA","JUPITER ISLAND","")
        ,("FLORIDA","MIAMI","")
        ,("FLORIDA","TBD","")
        ,("FLORIDA","WEST PALM BEACH","")
        ,("GEORGIA","ATLANTA","")
        ,("GEORGIA","DARIEN","")
        ,("GEORGIA","SAVANNAH","")
        ,("GEORGIA","THOMASVILLE","")
        ,("HAWAII","HONLULU","")
        ,("HAWAII","HONOLULU","")
        ,("ILLINOIS","CARY","")
        ,("ILLINOIS","CHICAGO","")
        ,("IOWA","DES MOINES","")
        ,("LOUISIANA","BATON ROUGE","")
        ,("MAINE","BRUNSWICK","")
        ,("MAINE","WASHINGTON COUNTY","")
        ,("MASSACHUSETTS","BOSTON","")
        ,("MASSACHUSETTS","VINEYARD HAVEN","")
        ,("MICHIGAN","GRAND RAPIDS","")
        ,("MICHIGAN","MARQUETTE","")
        ,("MICHIGAN","OWOSSO","")
        ,("MINNESOTA","KARLSTAD","")
        ,("MINNESOTA","MINNEAPOLIS","")
        ,("MINNESOTA","WABASHA","")
        ,("MISSISSIPPI","CAMP SHELBY","")
        ,("MISSOURI","ST. LOUIS","")
        ,("NEVADA","MINDEN","")
        ,("NEW HAMPSHIRE","CONCORD","")
        ,("NEW JERSEY","CHESTER","")
        ,("NEW YORK","ADIRONDACKS/KEENE VALLEY","")
        ,("NEW YORK","COLD SPRING HARBOR","")
        ,("NEW YORK","KEENE VALLEY","")
        ,("NEW YORK","LONG ISLAND","")
        ,("NEW YORK","LONG ISLAND CITY","")
        ,("NEW YORK","TROY","")
        ,("NORTH CAROLINA","DURHAM","")
        ,("OHIO","DUBLIN","")
        ,("OKLAHOMA","NEAR PAWHUSKA","")
        ,("OKLAHOMA","TULSA","")
        ,("PENNSYLVANIA","CONSHOHOCKEN","")
        ,("PENNSYLVANIA","HARRISBURG","")
        ,("PENNSYLVANIA","MEADVILLE","")
        ,("RHODE ISLAND","PROVIDENCE","")
        ,("SOUTH CAROLINA","COLUMBIA","")
        ,("TENNESSEE","NASHVILLE","")
        ,("TEXAS","CANYON","")
        ,("TEXAS","CORPUS CHRISTI","")
        ,("TEXAS","MATAGORDA COUNTY","")
        ,("TEXAS","MISSION","")
        ,("TEXAS","SAN ANTONIO","")
        ,("TEXAS","SILSBEE","")
        ,("TEXAS","TEXAS CITY","")
        ,("VERMONT","MANCHESTER","")
        ,("VERMONT","MONTPELIER","")
        ,("VERMONT","WEST HAVEN","")
        ,("VIRGINIA","ARLINGTON","")
        ,("WYOMING","JACKSON","")
    ]


def test_zip():
    for us_city in us_cities:
        try:
            (state,city,zipcode) = us_city
            if us_states.has_key(state):
                print (city,state,getzipcode(city,us_states[state]))
        except:
             print ("Error: ",us_city)



def seevents():
	# 2015 events
	chicago=pytz.timezone("America/Chicago")
	start_2015 = datetime.datetime(2015,1,1,0,0,tzinfo=chicago)
	end_2015 = datetime.datetime(2016,1,1,0,0,tzinfo=chicago)
	end_first_week_2015 = datetime.datetime(2015,1,8,0,0,tzinfo=chicago)
	search = ZipcodeSearchEngine()
	# all events in first week of 2015
	evs = Event.objects.filter(begin_time__gte=start_2015, end_time__lte=end_first_week_2015)
	for e in evs:
		print("---------------------")
		print(e.title)
		print(e.master)
		print("BEGIN TIME: ", repr(e.begin_time))
		print("END TIME: ", repr(e.end_time))
		print("CITY: ", e.city)
		print("STATE: ", e.state)
		print("ZIP CODE: ", e.zip_code)
		print("COUNTRY: ", e.country)
		print("TIMEZONE ATTRIBUTE VALUE: ", e.timezone)
		# if e.state:
		# 	print("TIMEZONE FROM STATE: ", tz_lookup.get(e.state))
		if e.city and e.state:
			tz=city_to_tz(e.city, e.state)
			print("**************************")
			print("TIMEZONE FROM CITY/STATE: ")
			print(tz)
			print("")
		try:
			if e.city and e.state:
				results = search.by_city_and_state(e.city, e.state)
				if results:
					zipcode = results[0]
					print("FIRST ZIP RETURNED BY LOOKUP: ", zipcode.Zipcode)
		except Exception as e:
			print("*************** EXCEPTION **************")
			print("Could not get zip code because of: ", e)
			print("****************************************")
		print("---------------------")


def city_to_zip(city, state):
	search = ZipcodeSearchEngine()
	try:
		if city and state:
			results = search.by_city_and_state(city, state)
			if results:
				zipcode = results[0]
				# print("FIRST ZIP RETURNED BY LOOKUP: ", zipcode.Zipcode)
				return zipcode.Zipcode
	except Exception as e:
		print("*************** EXCEPTION **************")
		print("Could not get zip code because: ", e)
		print("****************************************")
		return None


def zip_to_tz(zipcode, filepath="./_data_tools/zipcode.csv"):
#	"""
#	DATA FORMAT of csv file:
#	"zip","city","state","latitude","longitude","timezone","dst"
#	"""
	# with open(filepath, encoding="ISO-8859-1") as f:
	# 	reader = csv.reader(f, delimiter=",")
	# 	d = list(reader)

	with open(filepath) as csvfile:
		reader2 = csv.DictReader(csvfile)
		d2 = list(reader2)
		# print(d2[0]['zip'], d2[0]['timezone'])
		# print("INSIDE WITH:::::::::::::::::::")
		# for row in reader2:
		# 	print("row['zip'] is ", row['zip'])
		# 	print("str(zipcode) is ", str(zipcode))
		# 	if row['zip'] == str(zipcode):
		# 		print("MATCH IN THE WITH")
		# 		return row['timezone']
			# print(row['zip'], row['timezone'])
	for p in d2:
		# print("outside with p['zip'] is ", p['zip'])
		if p['zip'] == str(zipcode):
			# print("MATCH OUTSIDE THE WITH")
			# return { 'timezone':p['timezone'], 'dst':p['dst'] }
			# we need longitude/latitude to get the actual time zone
			# (not just the offset), so return the whole dict:
			return p
	# print("str(zipcode)is ", str(zipcode))
	# print("len of d is ", len(d))
	# print("len of d[1:] is ", len(d[1:]))
	# print("")
	# for p in d[1:]:
	# 	zipcode = p[0].strip()
	# 	print("zipcode is ", zipcode)
	# 	city=p[1].strip()
	# 	print("city is ", city)
	# 	state=p[2].strip()
	# 	print("state is ", state)
	# 	latitude=p[3].strip()
	# 	print("latitude is ", latitude)
	# 	longitude=p[4].strip()
	# 	print("longitude is ", longitude)
	# 	timezone=p[5].strip()
	# 	print("timezone is ", timezone)
	# 	dst=p[6].strip()
	# 	print("dst is ", dst)
	# 	seven=p[7].strip()
	# 	print("seven is ", seven)

def city_to_tz(city, state):
	return zip_to_tz(city_to_zip(city, state))

# FIRST TEST A GROUP WITH PRINT ONLY
# THEN COMMENT BACK IN THE SAVE() LINE

# DONE SO FAR ON LOCAL:
# ALL EVENTS BEFORE 1998

# NEXT: FOR EVENT_TYPE='COURSE' or anything without city/state treat as Chicago time
def get_events():
	# 2015 events
	chicago=pytz.timezone("America/Chicago")
	start_2015 = datetime.datetime(2015,1,1,0,0,tzinfo=chicago)
	end_2015 = datetime.datetime(2016,1,1,0,0,tzinfo=chicago)
	end_first_week_2015 = datetime.datetime(2015,1,8,0,0,tzinfo=chicago)
	# start = datetime.datetime(2015,2,3,8,0,tzinfo=chicago)
	start = datetime.datetime(1997,1,1,0,0,tzinfo=chicago)
	end = datetime.datetime(2018,1,1,0,0,tzinfo=chicago)
	# all events in first week of 2015
	# need to specify both begin and end as greater than start to avoid case where
	# end time is earlier than begin time
	evs = Event.objects.filter(begin_time__gte=start, end_time__gte=start, end_time__lte=end, timezone=None)
	# evs = Event.objects.filter(begin_time__lte=start)
	# special case queries: end time is earlier than begin time
	return evs

# must prefetch the other needed data here otherwise script is way slow
def get_claims():
	chicago=pytz.timezone("America/Chicago")
	start = datetime.datetime(2016,1,1,0,0,tzinfo=chicago)
	end = datetime.datetime(2016,1,8,0,0,tzinfo=chicago)
	claims = Claim.objects.filter(begin_time__gte=start, end_time__gte=start, end_time__lte=end, timezone=None
		).select_related("event")
	# .prefetch_related("event__city", "event__state", "event__zip_code")
	return claims

def get_jobs():
	chicago=pytz.timezone("America/Chicago")
	start = datetime.datetime(2016,2,1,0,0,tzinfo=chicago)
	end = datetime.datetime(2016,3,1,0,0,tzinfo=chicago)
	jobs = Job.objects.filter(post_time__gte=start, make_inactive_time__gte=start, make_inactive_time__lte=end
		)
	# CAN'T QUERY ON MICROSECOND:
	#.exclude(post_time__microsecond=10101, make_inactive_time__microsecond=10101)
	return jobs

def get_cm_periods():
	chicago=pytz.timezone("America/Chicago")
	start = datetime.datetime(2015,12,31,0,0,tzinfo=chicago)
	end = datetime.datetime(2018,1,1,0,0,tzinfo=chicago)
	periods = CMPeriod.objects.filter(begin_time__gte=start, end_time__gte=start, end_time__lte=end
		)
	#.exclude(begin_time__microsecond=10101, end_time__microsecond=10101, grace_end_time__microsecond=10101)
		

	return periods

def get_cm_logs():
	chicago=pytz.timezone("America/Chicago")
	start = datetime.datetime(2014,12,31,0,0,tzinfo=chicago)
	end = datetime.datetime(2017,1,1,0,0,tzinfo=chicago)
	logs = Log.objects.filter(begin_time__gte=start, end_time__gte=start, end_time__lte=end
		)
	#.exclude(begin_time__microsecond=10101, end_time__microsecond=10101, reinstatement_end_time__microsecond=10101)
	return logs

# submissions Periods
def get_periods():
	chicago=pytz.timezone("America/Chicago")
	start = datetime.datetime(2014,12,31,0,0,tzinfo=chicago)
	end = datetime.datetime(2017,1,1,0,0,tzinfo=chicago)
	periods = Period.objects.filter(begin_time__gte=start, end_time__gte=start, end_time__lte=end
		)
	#.exclude(begin_time__microsecond=10101, end_time__microsecond=10101)
	return periods

# submissions Reviews
def get_reviews():
	chicago=pytz.timezone("America/Chicago")
	start = datetime.datetime(2016,1,1,0,0,tzinfo=chicago)
	end = datetime.datetime(2016,8,1,0,0,tzinfo=chicago)
	reviews = Review.objects.filter(deadline_time__gte=start, deadline_time__lte=end
		)
	#.exclude(deadline_time__microsecond=10101)
	return reviews

# to correct times in events: ADD the timezone offset based on the location
# right now the times are stored as UTC in django...when we change our local timezone
# setting to America/Chicago all the times will be knocked back 5 hours, so for Chicago
# events we need to add 5 hours -- (the timezone will be returned as -5) also put DST 
# logic to test for current date?? or just run scripts now before DST??

# IN ADDITION TO ADJUSTING BEGIN/END TIMES, ALSO SET THE TIMEZONE ATTRIBUTE
# script #1: adjust the event/cm time to agree with the event location

# SO FAR THE ACTUAL HOUR/MINUTE TIMES LOOK CORRECT (GIVEN THE CORRECT TIME ZONE)
# so we will probably not need to adjust hour/minute values -- just set the time zone
# on the datetiem object and on the timezone attribute

# SO WHAT THIS METHOD IS DOING WE DON'T NEED: (PROBABLY)
# or maybe we need this or case #2 -- NO
# for events and for django all we need is to set a timezone on the datetiem object and
# on the attribute, assuming the hour/min values are correct

# NEXT: EXCEPTIONS: 1. none or invalid city and/or state
# PUBLISHABLE
def up_date_events(event_list):
	tzw = tzwhere.tzwhere()
	tz=None
	print("")
	for e in event_list:
		if e.timezone:
			print(e.title)
			print(e.master)
			print(e.publish_status)
			print("Has timezone...skipped.")
			print("")
		else:
			if e.zip_code:
				tz=zip_to_tz(e.zip_code)
			else:
				if e.city and e.state:
					if e.city == 'Sacramento' and e.state == 'CA':
						# need to hard-code this because the zip returned by city_to_zip doesn't work for Sacramento
						zipcode = '94203'
						tz = zip_to_tz(zipcode)
						print("e.city sacramento tz is .............", tz)
						print("")
					else:
						tz=city_to_tz(e.city, e.state)
				elif e.event_type == 'ACTIVITY':
					try:
						zip_code = e.parent.content_live.event.zip_code
						if zip_code:
							tz=zip_to_tz(zip_code)
						else:
							city = e.parent.content_live.event.city
							state = e.parent.content_live.event.state
							if city and state:
								tz=city_to_tz(city, state)
					except:
						tz = None
			if tz:
				offset=tz['timezone']
				offset_delta=datetime.timedelta(hours=abs(int(offset)))
				# won't need this, can just call pytz methods:
				# dst_bool=bool(tz['dst'])
				longitude=float(tz['longitude'])
				latitude=float(tz['latitude'])
				olson_zone=tzw.tzNameAt(latitude, longitude)
				if olson_zone:
					tz_obj=pytz.timezone(olson_zone)
					y=e.begin_time.year
					m=e.begin_time.month
					d=e.begin_time.day
					beg_dst_datetime = tz_obj.localize(datetime.datetime(y,m,d))
					y=e.end_time.year
					m=e.end_time.month
					d=e.end_time.day
					end_dst_datetime = tz_obj.localize(datetime.datetime(y,m,d))
					beg_dst_offset=beg_dst_datetime.dst()
					# print("beg_dst_offset is ", beg_dst_offset)
					end_dst_offset=end_dst_datetime.dst()
					# print("end_dst_offset is ", end_dst_offset)
					# no, just set this to a string
					# or it converts automatically
					# e.timezone=timezone
					e.timezone=olson_zone
					# subtract dst offset from timezone offset to get total offset for that date
					# normally either subtract 0 hours (in winter) or 1 hour (in summer)
					beg_total_offset = offset_delta - beg_dst_offset
					end_total_offset = offset_delta - end_dst_offset
					print(e.title)
					print(e.master)
					print(e.publish_status)
					print(e.city, e.state)
					# print("Database Time zone dict: ", tz)
					# print("Total begin time offset: ", beg_total_offset)
					# print("Total end time offset: ", end_total_offset)
					print("Old begin_time: ", repr(e.begin_time))
					new_begin = e.begin_time + beg_total_offset
					e.begin_time = new_begin
					print("New begin_time (still UTC): ", repr(e.begin_time))
					print("Old end_time: ", repr(e.end_time))
					new_end = e.end_time + end_total_offset
					e.end_time = new_end
					print("New end_time (still UTC): ", repr(e.end_time))
					print("")
					e.save()
					if e.publish_status == 'PUBLISHED':
						try:
							e.solr_publish()
						except:
							print("")
							print("----------------------")
							print("######################")
							print("COULD NOT SOLOR PUBLISH")
							print(e)
							print("######################")
							print("----------------------")
							print("")
					# print(e.title)
					# print(e.city, e.state)
					# print("Local time zone on attribute: ", e.timezone)				
					# print("")
				else:
					print("tzwhere DID NOT RETURN TIME ZONE")
					print("********************************")
					print("")
			# else if tz is None
			else:
				# first check for state and do a generic timezone by state:
				if e.state:
					if e.state in PACIFIC_GROUP:
						e.timezone = PT.zone
						e.save()
					elif e.state in MOUNTAIN_GROUP:
						e.timezone = MT.zone
						e.save()
					elif e.state in CENTRAL_GROUP:
						e.timezone = CT.zone
						e.save()
					elif e.state in EASTERN_GROUP:
						e.timezone = ET.zone
						e.save()
					else:
						e.timezone =CT.zone
						e.save()
					if e.publish_status == 'PUBLISHED':
						try:
							e.solr_publish()
						except:
							pass
					print("GETTING TIME ZONE FROM STATE ONLY")
					print("")
				else:
					print("if no location info treat as Chicago time with Chicago time zone")
					# print("NO LOCATION INFO -- pull timezone dict from parent location or do nothing")
					tz_obj=pytz.timezone('America/Chicago')					
					if e.begin_time:
						print(e.title)
						offset = get_utc_offset(e.begin_time, tz_obj)
						offset = offset * -1
						# dst offset already coming from get utc offset
						# dst_offset = get_dst_offset(p.begin_time, tz_obj)
						# total_offset = offset - dst_offset
						print("Old begin_time: ", repr(e.begin_time))
						e.begin_time = e.begin_time + offset
						print("New begin_time (still UTC): ", repr(e.begin_time))
					else:
						print("NO BEGIN TIME.")
						pass
					if e.end_time:
						offset=get_utc_offset(e.end_time, tz_obj)
						# print("offset is ..........", offset)
						offset = offset * -1
						# print("offset * -1 is ........", offset)
						# dst_offset = get_dst_offset(p.end_time, tz_obj)
						# print("dst_offset is .........", dst_offset)
						# total_offset = offset - dst_offset
						# print("total offset is ........", total_offset)
						print("Old end_time: ", repr(e.end_time))
						e.end_time = e.end_time + offset
						print("New end_time (still UTC): ", repr(e.end_time))
					else:
						print("NO END TIME")
						pass
					# still set this to None to obviate the rest of the code
					e.timezone=tz_obj.zone
					e.save()
					if e.publish_status == 'PUBLISHED':
						e.solr_publish()
					# Don't set tz to None, now we want the next block to execute if we got a timezone
					# from the parent -- no do that in up_date_activities script
					# tz=None
					print("*******")
					print(e.title)
					print(e.master)
					print(e.publish_status)
					print("NO CITY AND/OR STATE")
				print("NO TIME ZONE DICT RETURNED")
				print("*******")
				print("")

# SAVE MODEL ON CLAIMS: OVERWRITES VALUES SET ON THE CLAIM WITH (potentially empty)
# values from the associated event -- so in the script set the values on the event?
# or just change the save method to do an "or" self.begin_time or self.event.begin_time
# so that it will take the self value first, and only if it doesn't exist will it overwrite 
# the field with the event value

# NOT PUBLISHABLE
def up_date_claims(claims):
	tzw = tzwhere.tzwhere()
	tz=None
	print("")
	for c in claims:
		if c.timezone:
			print(c.title)
			print("Has timezone...skipped.")
			print("")
		# NOT LIKE THIS -- IT WRITES A TIMEZONE WITHOUT UPDATING THE TIMES:
		# elif c.event and c.event.timezone:
		# 	c.timezone = c.event.timezone
		# 	c.save()
		else:
			if c.event and c.event.zip_code:
				tz=zip_to_tz(c.event.zip_code)
			else:
				if c.city and c.state:
					if c.city == 'Sacramento' and c.state == 'CA':
						# need to hard-code this because the zip returned by city_to_zip doesn't work for Sacramento
						zipcode = '94203'
						tz = zip_to_tz(zipcode)
						print("c.city sacramento tz is .............", tz)
					else:
						tz=city_to_tz(c.city, c.state)
				elif c.event and c.event.city and c.event.state:
					if c.event.city == 'Sacramento' and c.event.state == 'CA':
						# need to hard-code this because the zip returned by city_to_zip doesn't work for Sacramento
						zipcode = '94203'
						tz = zip_to_tz(zipcode)
						print("c.event.city sacramento tz is .............", tz)
					else:
						tz=city_to_tz(c.event.city, c.event.state)
			if tz:
				offset=tz['timezone']
				offset_delta=datetime.timedelta(hours=abs(int(offset)))
				longitude=float(tz['longitude'])
				latitude=float(tz['latitude'])
				olson_zone=tzw.tzNameAt(latitude, longitude)
				print("OLSON ZONE IS .......", olson_zone)
				if olson_zone:
					tz_obj=pytz.timezone(olson_zone)
					print(c.title)
					if c.begin_time:
						y=c.begin_time.year
						m=c.begin_time.month
						d=c.begin_time.day
						beg_dst_datetime = tz_obj.localize(datetime.datetime(y,m,d))
						beg_dst_offset=beg_dst_datetime.dst()
						beg_total_offset = offset_delta - beg_dst_offset
						print("Old begin_time: ", repr(c.begin_time))
						new_begin = c.begin_time + beg_total_offset
						c.begin_time = new_begin
						print("New begin_time (still UTC): ", repr(c.begin_time))
					if c.end_time:
						y=c.end_time.year
						m=c.end_time.month
						d=c.end_time.day
						end_dst_datetime = tz_obj.localize(datetime.datetime(y,m,d))
						end_dst_offset=end_dst_datetime.dst()
						end_total_offset = offset_delta - end_dst_offset
						print("Old end_time: ", repr(c.end_time))
						new_end = c.end_time + end_total_offset
						c.end_time = new_end
						print("New end_time (still UTC): ", repr(c.end_time))
					c.timezone=olson_zone
					print("c.timezone is ..... ", c.timezone)
					c.save()
					print("Local time zone on attribute: ", c.timezone)				
					print("")
				else:
					print("tzwhere DID NOT RETURN TIME ZONE")
					print("********************************")
					print("")					
			# else if not tz
			else:
				# first check for state and do a generic timezone by state:
				if c.event and c.event.state:
					state=c.event.state
					if state in PACIFIC_GROUP:
						c.timezone = PT.zone
						c.save()
					elif state in MOUNTAIN_GROUP:
						c.timezone = MT.zone
						c.save()
					elif state in CENTRAL_GROUP:
						c.timezone = CT.zone
						c.save()
					elif state in EASTERN_GROUP:
						c.timezone = ET.zone
						c.save()
					else:
						c.timezone = CT.zone
						c.save()
					print("Got timezone from state only")
					print("")
				else:
					print("if no location info treat as Chicago time with Chicago time zone")
					# print("NO LOCATION INFO OR CAN'T DERIVE TIME ZONE -- DO NOTHING")
					tz_obj=pytz.timezone('America/Chicago')
					if c.begin_time:
						# print(c.title)
						offset = get_utc_offset(c.begin_time, tz_obj)
						offset = offset * -1
						# dst offset already coming from get utc offset
						# dst_offset = get_dst_offset(p.begin_time, tz_obj)
						# total_offset = offset - dst_offset
						print("Old begin_time: ", repr(c.begin_time))
						c.begin_time = c.begin_time + offset
						print("New begin_time (still UTC): ", repr(c.begin_time))
					else:
						print("NO BEGIN TIME.")
						pass
					if c.end_time:
						offset=get_utc_offset(c.end_time, tz_obj)
						# print("offset is ..........", offset)
						offset = offset * -1
						# print("offset * -1 is ........", offset)
						# dst_offset = get_dst_offset(p.end_time, tz_obj)
						# print("dst_offset is .........", dst_offset)
						# total_offset = offset - dst_offset
						# print("total offset is ........", total_offset)
						print("Old end_time: ", repr(c.end_time))
						c.end_time = c.end_time + offset
						print("New end_time (still UTC): ", repr(c.end_time))
					else:
						print("NO END TIME")
						pass
					# still set this to None to obviate the rest of the code
					c.timezone=tz_obj.zone
					print(" in Chicago time c.timezone is .......", c.timezone)
					c.save()
					print("after save c.timezone is ........", c.timezone)
					# tz=None
					print("*******")
					print(c.title)
					print("NO CITY AND/OR STATE")
				print("NO TIME ZONE DICT RETURNED")
				print("*******")
				print("")


def sync_claim_to_event(claims):
	for c in claims:
		# print("")
		if c.event and c.timezone and c.event.timezone:
			claim_zone_string = c.timezone
			event_zone_string = c.event.timezone
			the_event = c.event			
			if claim_zone_string == event_zone_string:
				tz_obj=pytz.timezone(claim_zone_string)
				if c.begin_time and the_event.begin_time:
					claim_begin = c.begin_time
					event_begin = the_event.begin_time
					offset = get_utc_offset(claim_begin, tz_obj)
					offset = offset * -1
					if event_begin == claim_begin + offset:
						# print("Old begin_time: ", repr(claim_begin))
						c.begin_time = c.begin_time + offset
						c.save()
						# print("New begin_time (still UTC): ", repr(c.begin_time))
				else:
					# print("NO BEGIN TIMES.")
					pass
				if c.end_time and the_event.end_time:
					claim_end = c.end_time
					event_end = the_event.end_time
					offset=get_utc_offset(claim_end, tz_obj)
					offset = offset * -1
					if event_end == claim_end + offset:
						# print("Old end_time: ", repr(claim_end))
						c.end_time = c.end_time + offset
						c.save()
						# print("New end_time (still UTC): ", repr(c.end_time))
				else:
					# print("NO END TIMES")
					pass
			else:
				# print("TIME ZONES ARE UNEQUAL")
				pass
		else:
			# print("EITHER NO EVENT OR MISSING TIME ZONE(S)")
			pass



# pass in a datetime object and a timezone object
def get_dst_offset(dt_obj, tz_obj):
	y=dt_obj.year
	m=dt_obj.month
	d=dt_obj.day
	loc_dt = tz_obj.localize(datetime.datetime(y,m,d))
	dst_offset=loc_dt.dst()
	return dst_offset

def get_utc_offset(dt_obj, tz_obj):
	naive_dt=timezone.make_naive(dt_obj)
	loc_dt=tz_obj.localize(naive_dt)
	utc_offset=loc_dt.utcoffset()
	return utc_offset

# PUBLISHABLE
def up_date_jobs(jobs):
	tz_obj=pytz.timezone('America/Chicago')
	# print("")
	for j in jobs:
		post_flag = j.post_time.microsecond==10101 if j.post_time else False
		make_flag=j.make_inactive_time.microsecond==10101 if j.make_inactive_time else False
		micro_flag = datetime.timedelta(microseconds=10101)
		if j.post_time and not j.post_time.microsecond==10101:
			# print(j)
			# print(j.master)
			# print(j.publish_status)
			offset = get_utc_offset(j.post_time, tz_obj)
			# print("offset is .............", offset)
			# make offset positive
			offset = offset * -1
			# print("offset * -1 is ........", offset)
			# print("Old post_time: ", repr(j.post_time))
			new_post = j.post_time + offset
			j.post_time = new_post
			# print("New post_time (still UTC): ", repr(j.post_time))			
			j.post_time = j.post_time + micro_flag
			j.save()
			if j.publish_status == 'PUBLISHED':
				try:
					j.solr_publish()
				except:
					print("")
					print("----------------------")
					print("######################")
					print("COULD NOT SOLOR PUBLISH")
					print(j)
					print("######################")
					print("----------------------")
					print("")
		else:
			print("Has microsecond flag...already updated.") if post_flag else print("NO POST TIME")
		if j.make_inactive_time and not j.make_inactive_time.microsecond==10101:
			offset=get_utc_offset(j.make_inactive_time, tz_obj)
			offset = offset * -1
			# make_dst_offset = get_dst_offset(j.make_inactive_time, tz_obj)
			# make_total_offset = offset - make_dst_offset
			# print("Old make_inactive_time: ", repr(j.make_inactive_time))
			new_inactive = j.make_inactive_time + offset
			j.make_inactive_time = new_inactive
			# print("New make_inactive_time (still UTC): ", repr(j.make_inactive_time))
			j.make_inactive_time = j.make_inactive_time + micro_flag
			j.save()
			if j.publish_status == 'PUBLISHED':
				try:
					j.solr_publish()
				except:
					print("")
					print("----------------------")
					print("######################")
					print("COULD NOT SOLOR PUBLISH")
					print(j)
					print("######################")
					print("----------------------")
					print("")
		else:
			print("Has microsecond flag...already updated.") if make_flag else print("NO MAKE INACTIVE TIME")
		# print("")

# NOT PUBLISHABLE
def up_date_cm_periods(periods):
	tz_obj=pytz.timezone('America/Chicago')
	# print("")
	for p in periods:
		begin_flag = p.begin_time.microsecond==10101 if p.begin_time else False
		end_flag = p.end_time.microsecond==10101 if p.end_time else False
		grace_flag = p.grace_end_time.microsecond==10101 if p.grace_end_time else False
		micro_flag = datetime.timedelta(microseconds=10101)
		if p.begin_time and not p.begin_time.microsecond==10101:
			# print(p)
			offset = get_utc_offset(p.begin_time, tz_obj)
			offset = offset * -1
			# dst offset already coming from get utc offset
			# dst_offset = get_dst_offset(p.begin_time, tz_obj)
			# total_offset = offset - dst_offset
			# print("Old begin_time: ", repr(p.begin_time))
			p.begin_time = p.begin_time + offset
			# print("New begin_time (still UTC): ", repr(p.begin_time))			
			p.begin_time = p.begin_time + micro_flag
			p.save()
		else:
			print("Has microsecond flag...already updated.") if begin_flag else print("NO BEGIN TIME")
		if p.end_time and not p.end_time.microsecond==10101:
			offset=get_utc_offset(p.end_time, tz_obj)
			# print("offset is ..........", offset)
			offset = offset * -1
			# print("offset * -1 is ........", offset)
			# dst_offset = get_dst_offset(p.end_time, tz_obj)
			# print("dst_offset is .........", dst_offset)
			# total_offset = offset - dst_offset
			# print("total offset is ........", total_offset)
			# print("Old end_time: ", repr(p.end_time))
			p.end_time = p.end_time + offset
			# print("New end_time (still UTC): ", repr(p.end_time))
			p.end_time = p.end_time + micro_flag
			p.save()
		else:
			print("Has microsecond flag...already updated.") if end_flag else print("NO END TIME")
		if p.grace_end_time and not p.grace_end_time.microsecond==10101:
			offset=get_utc_offset(p.grace_end_time, tz_obj)
			# print("offset is ..........", offset)
			offset = offset * -1
			# print("offset * -1 is ........", offset)
			# dst_offset = get_dst_offset(p.grace_end_time, tz_obj)
			# print("dst_offset is .........", dst_offset)
			# total_offset = offset - dst_offset
			# print("total offset is ........", total_offset)
			# print("Old grace_end_time: ", repr(p.grace_end_time))
			p.grace_end_time = p.grace_end_time + offset
			# print("New grace_end_time (still UTC): ", repr(p.grace_end_time))
			p.grace_end_time = p.grace_end_time + micro_flag
			p.save()
		else:
			print("Has microsecond flag...already updated.") if grace_flag else print("NO GRACE END TIME")
		# print("")

# NOT PUBLISHABLE
def up_date_cm_logs(logs):
	tz_obj=pytz.timezone('America/Chicago')
	# print("")
	for l in logs:
		begin_flag = l.begin_time.microsecond==10101 if l.begin_time else False
		end_flag = l.end_time.microsecond==10101 if l.end_time else False
		reinstatement_flag = l.reinstatement_end_time.microsecond==10101 if l.reinstatement_end_time else False
		micro_flag = datetime.timedelta(microseconds=10101)
		if l.begin_time and not l.begin_time.microsecond==10101:
			# print(l)
			offset = get_utc_offset(l.begin_time, tz_obj)
			offset = offset * -1
			# print("Old begin_time: ", repr(l.begin_time))
			l.begin_time = l.begin_time + offset
			# print("New begin_time (still UTC): ", repr(l.begin_time))			
			l.begin_time = l.begin_time + micro_flag
			l.save()
		else:
			print("Has microsecond flag...already updated.") if begin_flag else print("NO BEGIN TIME")
		if l.end_time and not l.end_time.microsecond==10101:
			offset=get_utc_offset(l.end_time, tz_obj)
			# print("offset is ..........", offset)
			offset = offset * -1
			# print("offset * -1 is ........", offset)
			# print("Old end_time: ", repr(l.end_time))
			l.end_time = l.end_time + offset
			# print("New end_time (still UTC): ", repr(l.end_time))
			l.end_time = l.end_time + micro_flag
			l.save()
		else:
			print("Has microsecond flag...already updated.") if end_flag else print("NO END TIME")
		if l.reinstatement_end_time and not l.reinstatement_end_time.microsecond==10101:
			offset=get_utc_offset(l.reinstatement_end_time, tz_obj)
			# print("offset is ..........", offset)
			offset = offset * -1
			# print("offset * -1 is ........", offset)
			# print("Old grace_end_time: ", repr(l.reinstatement_end_time))
			l.reinstatement_end_time = l.reinstatement_end_time + offset
			# print("New grace_end_time (still UTC): ", repr(l.reinstatement_end_time))
			l.reinstatement_end_time = l.reinstatement_end_time + micro_flag
			l.save()
		else:
			print("Has microsecond flag...already updated.") if reinstatement_flag else print("NO REINSTATEMENT END TIME")
		# print("")

# SUBMISSIONS PERIODS (NOT CM)
# NOT PUBLISHABLE
def up_date_periods(periods):
	tz_obj=pytz.timezone('America/Chicago')
	# print("")
	for p in periods:
		begin_flag = p.begin_time.microsecond==10101 if p.begin_time else False
		end_flag = p.end_time.microsecond==10101 if p.end_time else False
		micro_flag = datetime.timedelta(microseconds=10101)
		if p.begin_time and not p.begin_time.microsecond==10101:
			# print(p)
			offset = get_utc_offset(p.begin_time, tz_obj)
			offset = offset * -1
			# dst offset already coming from get utc offset
			# dst_offset = get_dst_offset(p.begin_time, tz_obj)
			# total_offset = offset - dst_offset
			# print("Old begin_time: ", repr(p.begin_time))
			p.begin_time = p.begin_time + offset
			# print("New begin_time (still UTC): ", repr(p.begin_time))			
			p.begin_time = p.begin_time + micro_flag
			p.save()
		else:
			print("Has microsecond flag...already updated.") if begin_flag else print("NO BEGIN TIME")
		if p.end_time and not p.end_time.microsecond==10101:
			offset=get_utc_offset(p.end_time, tz_obj)
			# print("offset is ..........", offset)
			offset = offset * -1
			# print("offset * -1 is ........", offset)
			# dst_offset = get_dst_offset(p.end_time, tz_obj)
			# print("dst_offset is .........", dst_offset)
			# total_offset = offset - dst_offset
			# print("total offset is ........", total_offset)
			# print("Old end_time: ", repr(p.end_time))
			p.end_time = p.end_time + offset
			# print("New end_time (still UTC): ", repr(p.end_time))
			p.end_time = p.end_time + micro_flag
			p.save()
		else:
			print("Has microsecond flag...already updated.") if end_flag else print("NO END TIME")
		# print("")

# NOT PUBLISHABLE
def up_date_reviews(reviews):
	tz_obj=pytz.timezone('America/Chicago')
	# print("")
	for r in reviews:
		deadline_flag = r.deadline_time.microsecond==10101 if r.deadline_time else False
		micro_flag = datetime.timedelta(microseconds=10101)
		if r.deadline_time and not r.deadline_time.microsecond==10101:
			# print(r)
			offset = get_utc_offset(r.deadline_time, tz_obj)
			offset = offset * -1
			# dst offset already coming from get utc offset
			# dst_offset = get_dst_offset(p.begin_time, tz_obj)
			# total_offset = offset - dst_offset
			# print("Old deadline_time: ", repr(r.deadline_time))
			r.deadline_time = r.deadline_time + offset
			# print("New deadline_time (still UTC): ", repr(r.deadline_time))			
			r.deadline_time = r.deadline_time + micro_flag
			r.save()
		else:
			print("Has microsecond flag...already updated.") if deadline_flag else print("NO DEADLINE TIME")
		# print("")

			# construct the datetime in pytz from:
			# date time timezone

# use pytz to do dst modification of offset?
# construct a pytz datetime with the time/timezone and then make naive?
# and compare to the orginal UTC time made naive?
# tz = pytz.timezone('America/Chicago')
# now = datetime.now(tz)

# SCRIPT #2: Adjust times that were entered assuming Central (but saved as UTC)
# by the central offset (+5 (summer time) or +6 (winter time)) hours -- still need daylight savings here

# OR -- we do want to change the hour -- and leave the timezone as UTC in database? and just put
# the timezone on the attribute?? so we need both of these methods


# method for testing getting timezone from latitude and longitude
def add_zone(event_list):
	tzw = tzwhere.tzwhere()
	zone=tzw.tzNameAt(35.29, -89.66)
	print("time zone is: ", zone)
	print("")
	for e in event_list:
		if e.city and e.state:
			tz=city_to_tz(e.city, e.state)
			if tz:
				# offset=tz['timezone']
				longitude=float(tz['longitude'])
				latitude=float(tz['latitude'])
				zone=tzw.tzNameAt(latitude, longitude)
				timezone=pytz.timezone(zone)
				print(e.title)
				print(e.city, e.state)
				print("Time zone: ", timezone)
				print("")
				# construct a new datetime object with old hour/min and new timezone
				# and set this as the new value of the begin_time attribute
				# new_begin = timezone.localize

def testcm(claims):
	print("")
	for c in claims:
		print(c.title)
		print(c.city)
		print(c.state)
		if c.event:
			print("ON EVENT:")
			print(c.event.city)
			print(c.event.state)
		print("")


# Updating events in 365-day chunks 2014 down to 1997
def update_events_by_year():
	chicago=pytz.timezone("America/Chicago")
	for i in range(0,2017-1996):
		td = datetime.timedelta(days=i*365)
		start = datetime.datetime(2017,1,1,0,0,tzinfo=chicago) - td
		end = datetime.datetime(2018,1,1,0,0,tzinfo=chicago) - td
		evs = Event.objects.filter(begin_time__gte=start, end_time__gte=start, end_time__lte=end, timezone=None)
		print("STARTING %s events update" % (2017-i))
		up_date_events(evs)
		print("FINISHED %s events update" % (2017-i))
		print("")

# updating claims by 30-day chunks down to 1997
def update_claims_by_month():
	chicago=pytz.timezone("America/Chicago")
	for i in range(0,12*(2017-1996)):
		td = datetime.timedelta(days=i*31)
		start = datetime.datetime(2017,12,1,0,0,tzinfo=chicago) - td
		end = datetime.datetime(2018,1,1,0,0,tzinfo=chicago) - td
		claims = Claim.objects.filter(begin_time__gte=start, end_time__gte=start, end_time__lte=end, timezone=None
			).select_related("event")
		print("STARTING claims update in 31-day period starting approx. %s years before 2017-12-1" % ((i*31)/365))
		up_date_claims(claims)
		print("FINISHED claims update")
		print("")

# AFTER RUNNING THE ABOVE MAY HAVE TO RUN AGAIN ON ALL RECORDS TO CATCH EDGE CASES
# (WHEN THE END TIME IS OUTSIDE OF THE WINDOW) - the query will only pick up non-timezone
# records so should be much smaller number

def update_claims_from_events():
	claims=Claim.objects.all()
	sync_claim_to_event(claims)