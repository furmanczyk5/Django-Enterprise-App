import django
django.setup()

import warnings
warnings.filterwarnings('ignore')

from myapa.models import IndividualContact, IndividualProfile

def update_sharing(max=None):
    if max:
        qs = IndividualContact.objects.only("id")[:max]
    else:
        qs = IndividualContact.objects.only("id")
    # print(qs)

    for i in qs:
        if not i.user:
            print("WARNING! No user for contact id: " + str(i.id))
        else:
            try:
                if not hasattr(i, "individualprofile") or not i.individualprofile:
                    i.individualprofile = IndividualProfile.objects.create(contact=i)
                    print("Creating NEW profile for: " + i.user.username)

                json = i.get_imis_contact_preferences()
                exclude_directory = json[0]["EXCL_WEBSITE"]

                if exclude_directory and i.individualprofile.share_profile == "PRIVATE":
                    # NO CHANGE
                    pass

                elif exclude_directory and i.individualprofile.share_profile != "PRIVATE":
                    print("WARNING! --------------------------------------------------------------")
                    print("User " + i.user.username + " was excluded from the directory, but has shared profile.... is now INCLUDED in directory.")
                    print("-----------------------------------------------------------------------")
                    # NO CHANGE
                    pass


                elif not exclude_directory and i.individualprofile.share_profile == "PRIVATE" and (
                        i.individualprofile.slug is not None or
                        i.individualprofile.share_contact == "PRIVATE" or
                        i.individualprofile.share_bio == "PRIVATE" or
                        i.individualprofile.share_social == "PRIVATE" or
                        i.individualprofile.share_leadership == "PRIVATE" or
                        i.individualprofile.share_education == "PRIVATE" or
                        i.individualprofile.share_jobs == "PRIVATE" or
                        i.individualprofile.share_events == "PRIVATE" or
                        i.individualprofile.share_resume == "PRIVATE" or
                        i.individualprofile.share_conference == "PRIVATE" or
                        i.individualprofile.share_advocacy == "PRIVATE"
                    ):
                    print("WARNING! --------------------------------------------------------------")
                    print("User " + i.user.username + " was included from the directory, but has updating sharing with PRIVATE somewhere.... is now EXCLUDED from the directory.")
                    print("-----------------------------------------------------------------------")
                    # NO CHANGE
                    pass
                elif not exclude_directory and i.individualprofile.share_profile == "PRIVATE":
                    print("User " + i .user.username + " updated from PRIVATE to MEMBER")
                    i.individualprofile.share_profile = "MEMBER"
                    i.individualprofile.share_contact = "MEMBER" 
                    i.individualprofile.share_bio = "PRIVATE" 
                    i.individualprofile.share_social = "PRIVATE" 
                    i.individualprofile.share_leadership = "PRIVATE" 
                    i.individualprofile.share_education = "PRIVATE" 
                    i.individualprofile.share_jobs = "PRIVATE" 
                    i.individualprofile.share_events = "PRIVATE" 
                    i.individualprofile.share_resume = "PRIVATE" 
                    i.individualprofile.share_conference = "PRIVATE" 
                    i.individualprofile.share_advocacy = "PRIVATE"
                    i.individualprofile.save()

            except Exception as e:
                print("ERROR! ----------------------------------------------------------------")
                print(str(e))
                print("-----------------------------------------------------------------------")


