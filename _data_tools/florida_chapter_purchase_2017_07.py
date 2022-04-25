from store.models import *

def purchase_fix(): 
    users_without_d1 = set([])
    users_without_d2 = set([])
    users_without_d3 = set([])
    users_without_d4 = set([])
    users_without_d5 = set([])
    users_without_d6 = set([])

    d1 = Purchase.objects.filter(product__code='EVENT_FL17', option__code__in=['FL1','FL2','FL3','FL4','FL5','FL8','FL9','FL13'], status='A', quantity__gte=1).exclude(order__isnull=True)

    d2 = Purchase.objects.filter(product__code='EVENT_FL17', option__code__in=['FL1','FL2','FL3','FL4','FL5','FL12','FL13'], status='A', quantity__gte=1).exclude(order__isnull=True)

    d3 = Purchase.objects.filter(product__code='EVENT_FL17', option__code__in=['FL1','FL2','FL3','FL4','FL5','FL6','FL7'], status='A', quantity__gte=1).exclude(order__isnull=True)

    d4 = Purchase.objects.filter(product__code='EVENT_FL17', option__code__in=['FL1','FL2','FL3','FL4','FL5','FL6', 'FL7','FL8'], status='A', quantity__gte=1).exclude(order__isnull=True)

    d5 = Purchase.objects.filter(product__code='EVENT_FL17', option__code__in=['FL1','FL2','FL3','FL4','FL5','FL8','FL9'], status='A', quantity__gte=1).exclude(order__isnull=True)

    d6 = Purchase.objects.filter(product__code='EVENT_FL17', option__code__in=['FL1','FL2','FL3','FL4','FL5','FL8','FL9','FL13'], status='A', quantity__gte=1).exclude(order__isnull=True)

    for x in d1:
        user = x.user
        if not Purchase.objects.filter(product__code='ACTIVITY_FL17_D1', user=user).exclude(order__isnull=True):
            if Purchase.objects.filter(product__code='ACTIVITY_FL17_E3', user=user).exclude(order__isnull=True):
                users_without_d1.add(user.username)

    for x in d2:
        user = x.user
        if not Purchase.objects.filter(product__code='ACTIVITY_FL17_D2', user=user).exclude(order__isnull=True):
            if Purchase.objects.filter(product__code='ACTIVITY_FL17_E1', user=user).exclude(order__isnull=True):
                users_without_d2.add(user.username)

    for x in d3:
        user = x.user
        if not Purchase.objects.filter(product__code='ACTIVITY_FL17_D3', user=user).exclude(order__isnull=True):
            if Purchase.objects.filter(product__code='ACTIVITY_FL17_I2', user=user).exclude(order__isnull=True):
                users_without_d3.add(user.username)

    for x in d4:
        user = x.user
        if not Purchase.objects.filter(product__code='ACTIVITY_FL17_D4', user=user).exclude(order__isnull=True):
            if Purchase.objects.filter(product__code='ACTIVITY_FL17_E2', user=user).exclude(order__isnull=True):
                users_without_d4.add(user.username)

    for x in d5:
        user = x.user
        if not Purchase.objects.filter(product__code='ACTIVITY_FL17_D5', user=user).exclude(order__isnull=True):
            if Purchase.objects.filter(product__code='ACTIVITY_FL17_I3', user=user).exclude(order__isnull=True):
                users_without_d5.add(user.username)

    for x in d6:
        user = x.user
        if not Purchase.objects.filter(product__code='ACTIVITY_FL17_D6', user=user).exclude(order__isnull=True):
            if Purchase.objects.filter(product__code='ACTIVITY_FL17_E3', user=user).exclude(order__isnull=True):
                users_without_d6.add(user.username)

    print('users without d1')
    print('count: ' + str(len(users_without_d1)))
    print(str(users_without_d1))
    print('-------------------')

    print('users without d2')
    print('count: ' + str(len(users_without_d2)))
    print(str(users_without_d2))
    print('-------------------')

    print('users without d3')
    print('count: ' + str(len(users_without_d3)))
    print(str(users_without_d3))
    print('-------------------')

    print('users without d4')
    print('count: ' + str(len(users_without_d4)))
    print(str(users_without_d4))
    print('-------------------')

    print('users without d5')
    print('count: ' + str(len(users_without_d5)))
    print(str(users_without_d5))
    print('-------------------')

    print('users without d6')
    print('count: ' + str(len(users_without_d6)))
    print(str(users_without_d6))
    print('-------------------')


    print('users who should not have a drink ticket')

    no_ticket_d1 = set([])
    no_ticket_d2 = set([])
    no_ticket_d3 = set([])
    no_ticket_d4 = set([])
    no_ticket_d5 = set([])
    no_ticket_d6 = set([])

    d1_purchases = Purchase.objects.filter(product__code='ACTIVITY_FL17_D1', status='A', quantity__gte=1).exclude(order__isnull=True)
    d2_purchases = Purchase.objects.filter(product__code='ACTIVITY_FL17_D2', status='A', quantity__gte=1).exclude(order__isnull=True)
    d3_purchases = Purchase.objects.filter(product__code='ACTIVITY_FL17_D3', status='A', quantity__gte=1).exclude(order__isnull=True)
    d4_purchases = Purchase.objects.filter(product__code='ACTIVITY_FL17_D4', status='A', quantity__gte=1).exclude(order__isnull=True)
    d5_purchases = Purchase.objects.filter(product__code='ACTIVITY_FL17_D5', status='A', quantity__gte=1).exclude(order__isnull=True)
    d6_purchases = Purchase.objects.filter(product__code='ACTIVITY_FL17_D6', status='A', quantity__gte=1).exclude(order__isnull=True)

    for x in d1_purchases:
        if not Purchase.objects.filter(product__code='EVENT_FL17', option__code__in=['FL1','FL2','FL3','FL4','FL5','FL8','FL9','FL13'], status='A', quantity__gte=1, user = x.user).exclude(order__isnull=True):
            no_ticket_d1.add(x.user.username)

    for x in d2_purchases:
        if not Purchase.objects.filter(product__code='EVENT_FL17', option__code__in=['FL1','FL2','FL3','FL4','FL5','FL12','FL13'], status='A', quantity__gte=1, user = x.user).exclude(order__isnull=True):
            no_ticket_d1.add(x.user.username)

    for x in d3_purchases:
        if not Purchase.objects.filter(product__code='EVENT_FL17', option__code__in=['FL1','FL2','FL3','FL4','FL5','FL6','FL7'], status='A', quantity__gte=1, user = x.user).exclude(order__isnull=True):
            no_ticket_d1.add(x.user.username)

    for x in d4_purchases:
        if not Purchase.objects.filter(product__code='EVENT_FL17', option__code__in=['FL1','FL2','FL3','FL4','FL5','FL6', 'FL7','FL8'], status='A', quantity__gte=1, user = x.user).exclude(order__isnull=True):
            no_ticket_d1.add(x.user.username)

    for x in d5_purchases:
        if not Purchase.objects.filter(product__code='EVENT_FL17', option__code__in=['FL1','FL2','FL3','FL4','FL5','FL8','FL9'], status='A', quantity__gte=1, user = x.user).exclude(order__isnull=True):
            no_ticket_d1.add(x.user.username)

    for x in d6_purchases:
        if not Purchase.objects.filter(product__code='EVENT_FL17', option__code__in=['FL1','FL2','FL3','FL4','FL5','FL8','FL9','FL13'], status='A', quantity__gte=1, user = x.user).exclude(order__isnull=True):
            no_ticket_d1.add(x.user.username)

    print('users should not have a d1 ticket')
    print('count: ' + str(len(no_ticket_d1)))
    print(str(no_ticket_d1))
    print('-------------------')

    print('users should not have a d2 ticket')
    print('count: ' + str(len(no_ticket_d2)))
    print(str(no_ticket_d2))
    print('-------------------')

    print('users should not have a d3 ticket')
    print('count: ' + str(len(no_ticket_d3)))
    print(str(no_ticket_d3))
    print('-------------------')

    print('users should not have a d4 ticket')
    print('count: ' + str(len(no_ticket_d4)))
    print(str(no_ticket_d4))
    print('-------------------')

    print('users should not have a d5 ticket')
    print('count: ' + str(len(no_ticket_d5)))
    print(str(no_ticket_d5))
    print('-------------------')

    print('users should not have a d6 ticket')
    print('count: ' + str(len(no_ticket_d6)))
    print(str(no_ticket_d6))
    print('-------------------')
