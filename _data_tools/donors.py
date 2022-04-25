from django.db.models import Q
from django.contrib.auth.models import User

from imis.db_accessor import DbAccessor

from store.models import Donation
from imis.models import Giftreport, Activity
from myapa.templatetags.myapa_tags import get_django_purchase

# TO FIX DATA CORRUPTION (TRIBUTEE WRITTEN TO MULTIPLE RECORDS):
# 1. RUN donation_data_dump with wipe = True
# 2. RUN donation_data_dump with wipe = False

def donation_data_dump(donations=None, wipe=False):
    if not donations:
        donations = Donation.objects.filter(Q(is_anonymous=True) | Q(is_tribute=True))
    for d in donations:
        if d.purchase and d.purchase.submitted_time:
            st_date_only = d.purchase.submitted_time.replace(hour=0,minute=0,second=0,microsecond=0)
            print("st_date_only: ", st_date_only)
            imis_code = d.purchase.product.imis_code if d.purchase.product else None
            print("imis_code: ", imis_code)
            gs = Giftreport.objects.filter(
                id=d.purchase.contact.user.username,
                amount=d.purchase.amount,
                transactiondate=st_date_only,
                campaigncode=imis_code)
            print("gs is ", gs)
            count = gs.count()
            if count == 1:
                print("count is 1")
                g = gs.first()
                print("gift report object is ")
                print(g.__dict__)
                if d.is_anonymous:
                    if wipe:
                        g.listas = ""
                        g.save(update_fields=['listas'])
                    else:
                        update_anon("Anonymous", g.id, g.originaltransaction)
                        print("exactly 1 anon")
                else:
                    print("NOT ANONYMOUS SO WIPING LISTAS")
                    update_anon("", g.id, g.originaltransaction)
                if d.is_tribute:
                    if wipe:
                        g.memorialnametext = ""
                        g.memorialtributetype = ""
                        g.save(update_fields=['memorialnametext', 'memorialtributetype'])
                    else:
                        print("tribute honoree is ", d.tribute_honoree)
                        update_tribute(d.tribute_honoree, "HONOROF", g.id, g.originaltransaction)
                        print("exactly 1 trib")
                        act_note = "A tribute email was sent to %s" % d.tribute_email
                        update_tribute_email(act_note, g.id, g.originaltransaction)
                else:
                    print("it's not tribute so we're blanking out the tribute fields")
                    print("before blanking values are")
                    print(g.memorialnametext)
                    print(g.memorialtributetype)
                    update_tribute("", "", g.id, g.originaltransaction)
                    update_tribute_email("", g.id, g.originaltransaction)
            elif count > 1:
                print("count greater than 1 ")
                if d.is_anonymous:
                    print("IS ANONYMOUS")
                    if not wipe:
                        gs = gs.filter(listas="")
                    if gs:
                        if wipe:
                            for g in gs:
                                g.listas = ""
                                g.save(update_fields=['listas'])
                        else:
                            g = gs.first()
                            update_anon("Anonymous", g.id, g.originaltransaction)
                            print("more than 1 anon ", gs)
                if d.is_tribute:
                    if not wipe:
                        gs = gs.filter(memorialnametext="")
                    print("GS COUNT AFTER FILTER IS ------- ", gs.count())
                    if gs:
                        if wipe:
                            print("WIPING TRIBUTE DATA FOR COUNT > 1")
                            for g in gs:
                                print("memorialnametext: ", g.memorialnametext)
                                print("memorialtributetype: ", g.memorialtributetype)
                                g.memorialnametext = ""
                                g.memorialtributetype = ""
                                g.save(update_fields=['memorialnametext', 'memorialtributetype'])
                        else:
                            g = gs.first()
                            update_tribute(d.tribute_honoree, "HONOROF", g.id, g.originaltransaction)
                            act_note = "A tribute email was sent to %s" % d.tribute_email
                            update_tribute_email(act_note, g.id, g.originaltransaction)
                        # not sure if this was a data problem or not
                        # so commenting out for now
                        # if wipe:
                        #     if d.tribute_email:
                        #         act = Activity.objects.filter(
                        #             originating_trans_num=g.transactionnumber).first()
                        #         if act:
                        #             act.note = ""
                        #             act.save(update_fields=['note'])
                        #             print("activity is ", act)
        print("DONE ----------------- \n\n")
ddd=donation_data_dump


def update_tribute(nametext, tributetype, gr_id, orig_trans):
    query = """
     UPDATE G
     SET G.MEMORIALNAMETEXT = ?,
        G.MEMORIALTRIBUTETYPE = ?
    FROM Giftreport G
    INNER JOIN Activity A 
        ON A.originating_trans_num = G.originaltransaction
        AND A.other_id = G.id
     WHERE G.ID = ? AND G.ORIGINALTRANSACTION = ?
    """
    DbAccessor().execute(query, [nametext, tributetype, gr_id, orig_trans])


def update_tribute_email(act_note, gr_id, orig_trans):
    query = """
     UPDATE A
     SET A.NOTE = ?
    FROM Giftreport G
    INNER JOIN Activity A 
        ON A.originating_trans_num = G.originaltransaction
        AND A.other_id = G.id
     WHERE G.ID = ? AND G.ORIGINALTRANSACTION = ?
    """
    DbAccessor().execute(query, [act_note, gr_id, orig_trans])


def update_anon(listas, gr_id, orig_trans):
    query = """
     UPDATE G
     SET G.LISTAS = ?
    FROM Giftreport G
    INNER JOIN Activity A 
        ON A.originating_trans_num = G.originaltransaction
        AND A.other_id = G.id
     WHERE G.ID = ? AND G.ORIGINALTRANSACTION = ?
    """
    DbAccessor().execute(query, [listas, gr_id, orig_trans])
