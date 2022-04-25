from registrations.models import Attendee

def set_blank_badge_fields():

	for a in Attendee.objects.select_related("contact").all():

		if not a.badge_name or not a.badge_location:
			
			if not a.badge_name:
				a.badge_name = a.contact.first_name

			if not a.badge_location and (a.contact.city or a.contact.state):
				a.badge_location = "{0}, {1}".format(a.contact.city, a.contact.state)

			a.save()