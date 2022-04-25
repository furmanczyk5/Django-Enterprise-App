from cm.models import *
from imis.models import *


def cm_drop(ids_list=[]):
    """
    drops cm logs based on ids list. the log dropped is the is_current log associated with the user.
    """

    error_dict = {}
    missing_current_log = []
    for x in ids_list:
        try:
            logs = Log.objects.filter(contact__user__username=x, is_current=True).exclude(status="D")

            for log in logs:
                log.status='D'
                log.save()

                Subscriptions.aicp_drop(x, log.period.code)

            if not logs:
                missing_current_log.append(x)

        except Exception as e:
            error_dict[x] = str(e)
            continue

    print("ERRORS: "  + str(error_dict))
    print("----------------------------")
    print("MISSING CURRENT LOG: " + str(missing_current_log))

