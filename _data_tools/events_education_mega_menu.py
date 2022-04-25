from content.models.menu_item import MenuItem
from pages.models import LandingPage

# The master id of the landing page for /education/
EDUCATION_AND_EVENTS_MASTER_ID_LOCAL = 9156671
EDUCATION_AND_EVENTS_MASTER_ID_STAGING = 9156635
# EDUCATION_AND_EVENTS_MASTER_ID_PROD = ''
# The existing /events/ landing page, in case we need to revert
EVENTS_MASTER_ID = 9026571


def main(master_id):

    root_menu = MenuItem.get_root_menu()
    evts = next(x for x in root_menu if x.get_url() == '/events/')

    # Overview should now point to /education/ instead of /events/
    lp_edu = LandingPage.objects.get(publish_status="PUBLISHED", master_id=master_id)
    evts.master = lp_edu.master
    evts.save()

