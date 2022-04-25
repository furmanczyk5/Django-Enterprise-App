
from django.conf import settings
from django.utils import timezone

from cm.models import Claim, Log#, Period
from content.models import MessageText, ContentRelationship
# from exam.models import ENROLLED_STATUSES, ExamApplication
from learn.models import LearnCourseEvaluation


# Could this be better placed on a model, need to watch out for circular imports in that case
def get_eval_status(event, contact, claim=None, current_log=None):
    if contact:
        claim = claim or Claim.objects.filter(contact=contact, event=event, is_deleted=False).first()
        event_is_dupe = False

        if not claim:
            crs_from = ContentRelationship.objects.filter(
                content=event).prefetch_related(
                "content", "content__event", "content_master_related",
                "content_master_related__content",
                "content_master_related__content__event")
            crs_to = ContentRelationship.objects.filter(
                content_master_related=event.master).prefetch_related(
                "content", "content__event", "content_master_related",
                "content_master_related__content",
                "content_master_related__content__event")

            for cr in crs_from:
                content_versions = cr.content_master_related.content.all()
                # dupe_claim = Claim.objects.filter(
                #     contact=contact, event__in=content_versions)
                dupe_claim = Claim.objects.filter(
                    contact=contact, event__in=content_versions, is_deleted=False)
                if dupe_claim:
                    event_is_dupe = True
                    claim_from = dupe_claim
                    published_content = cr.content_master_related.content.filter(
                        publish_status="PUBLISHED").first()
                    # course_eval = LearnCourseEvaluation.objects.filter(
                    #     contact=contact,
                    #     content=published_content).first()
                    course_eval = LearnCourseEvaluation.objects.filter(
                        contact=contact,
                        content=published_content, is_deleted=False).first()
                    if course_eval:
                        from learn.views.log import hide_learn_course_eval
                        hide_learn_course_eval(course_eval)
                    break

            if not event_is_dupe:
                for cr in crs_to:
                    # dupe_claim = Claim.objects.filter(contact=contact,
                    #                                   event=cr.content.event)
                    dupe_claim = Claim.objects.filter(contact=contact,
                                                      event=cr.content.event, is_deleted=False)
                    if dupe_claim:
                        event_is_dupe = True
                        claim_to = dupe_claim
                        published_content = cr.content_master_related.content.filter(
                            publish_status="PUBLISHED").first()
                        # course_eval = LearnCourseEvaluation.objects.filter(
                        #     contact=contact,
                        #     content=published_content).first()
                        course_eval = LearnCourseEvaluation.objects.filter(
                            contact=contact,
                            content=published_content, is_deleted=False).first()
                        if course_eval:
                            from learn.views.log import hide_learn_course_eval
                            hide_learn_course_eval(course_eval)
                        break

        is_aicp = next(
            (True for g in contact.user.groups.all() if
             (g.name == "aicp-cm" or g.name == "reinstatement-cm")
             ), False
        )

        is_candidate = contact.is_aicp_candidate()
        log = current_log or Log.objects.filter(contact=contact, is_current=True).first() if is_aicp else None

        if not log:
            log = contact.get_cm_log()
    else:
        is_aicp = False
        is_candidate = False
        claim = None
        log = None
    c = is_candidate
    now = timezone.now()
    event_is_started = event.begin_time and event.begin_time < now
    event_has_cm = bool(event.cm_approved and event.cm_approved > 0)
    log_is_active = log and log.is_active()
    log_end_time = log and (log.reinstatement_end_time or log.end_time) # assume reinstatement_end_time is always later than end_time
    within_current_logging = log and (not claim or claim.log == log) and event_is_started and event.begin_time < log_end_time and event.end_time > log.begin_time

    eval_url = None # the url where the current user is alloved to evaluate this event
    eval_action = None # short string action user can take to evaluate this event
    eval_message = "" # short messgae describing user's status and relationship to this event
    eval_html = None # longer html for when more explanation is needed
    base_url = settings.PLANNING_SERVER_ADDRESS if \
        (isinstance(settings.PLANNING_SERVER_ADDRESS, str) and not settings.PLANNING_SERVER_ADDRESS.endswith('/')) \
        else settings.PLANNING_SERVER_ADDRESS[:-1]

    if not event_is_started:
        eval_url = "/events/event/{0}/".format(event.master_id)  # Route to details view
    elif not contact:
        eval_action = "LOGIN"
        eval_url = base_url + "/cm/log/claim/event/{0}/".format(event.master_id) # We still want to direct user to log this event (they will need to login anyway)
    elif claim and event_has_cm:
        if is_aicp or is_candidate:
            if within_current_logging and log_is_active:
                eval_action = "CLAIM_CM"
                eval_url = base_url + "/cm/log/claim/event/{0}/".format(event.master_id)
            else:
                eval_action = "VIEW_CM"
                eval_url = base_url + "/cm/log/claim/{0}/".format(claim.id)
                eval_message = "You cannot edit claims that are outside of your current %s period." % ("logging" if not c else "tracking")
        else:
            eval_action = "VIEW_CM"
            eval_url = base_url + "/cm/log/claim/{0}/".format(claim.id)
            eval_message = "You cannot edit claims that are outside of your current %s period." % ("logging" if not c else "tracking")
    else:
        if (is_aicp or is_candidate) and event_has_cm:
            if within_current_logging and log_is_active and not event_is_dupe:
                eval_action = "CLAIM_CM"
                eval_url = base_url + "/cm/log/claim/event/{0}/".format(event.master_id)
            elif event_is_dupe:
                eval_action = "EVALUATE"
                eval_url = base_url + "/events/event/{0}/".format(event.master_id)  # Route to details view
                eval_message = "You cannot %s duplicate education." % ("log" if not c else "track")
            else:
                eval_message = "This event is outside of your current %s period, but you may still evaluate it without claiming cm credits." % ("logging" if not c else "tracking")
                eval_action = "EVALUATE"
                eval_url = base_url + "/events/{0}/evaluation/".format(event.master_id)
        else:
            eval_action = "EVALUATE"
            eval_url = base_url + "/events/{0}/evaluation/".format(event.master_id)

    # WHEN IS THE MOST APPROPRIATE TIME TO SHOW THIS, DO WE JUST DIRECT USERS TO EVALUATE THIS SESSION?
    if not log_is_active:
        eval_html = MessageText.objects.filter(code="NO_ACTIVE_CM_LOG").first().text

    return {
        "claim": claim,
        "is_aicp": is_aicp,
        "is_candidate": is_candidate,
        "within_current_loggin_period": within_current_logging,
        "current_log": log,
        "log_is_active": log_is_active,
        "evaluation_url": eval_url,  # should route user here when trying to log credits/evaluate
        "evaluation_action": eval_action,  # CLAIM_CM, EVALUATE, or None
        "evaluation_message": eval_message,  # message to the user
        "evaluation_html": eval_html
    }
