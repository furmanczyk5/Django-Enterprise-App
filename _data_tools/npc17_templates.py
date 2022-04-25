"""Script to set all NPC17 Activities to the event-details.html template"""

from events.models import Activity

NPC_16_MASTER_ID = '9000321'
NPC_17_MASTER_ID = '9102340'
TEMPLATE = 'events/newtheme/event-details.html'


def main():
    Activity.objects.filter(
        parent__id__in=(
            NPC_16_MASTER_ID, NPC_17_MASTER_ID
        )
    ).update(template=TEMPLATE)


