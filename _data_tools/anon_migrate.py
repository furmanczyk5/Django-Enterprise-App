from myapa.models.contact import Contact

# step 1: create name and bios fields in contactrole model (migraitons)
# step 2: run the create contactroles script
# step 3: make contac
def anon_contactroles():
	"""
	creates contactrole anonymous records and deletes the existing contact record
	"""

	contacts = Contact.objects.filter(user__username = 'ANONYMOUS')
	
	print("there are {0} contacts to move...".format(contacts.count()))

	for contact in contacts:
		print("importing {0}".format(contact.first_name))

		if contact.contactrole.all():
			for contactrole in contact.contactrole.all():
				contactrole.first_name = contact.first_name
				contactrole.middle_name = contact.middle_name
				contactrole.last_name = contact.last_name
				contactrole.bio = contact.bio
				contactrole.email = contact.email
				contactrole.phone = contact.phone
				contactrole.company = contact.company
				contactrole.cell_phone = contact.cell_phone
				contactrole.save()

				print("successfully added contact values for anonymous contact")
		else:
			print("contact role does not exist for anonymous contact")
			
		contact.delete()