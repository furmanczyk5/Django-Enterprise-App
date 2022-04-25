from datetime import timedelta
from decimal import Decimal
from unittest import mock
from unittest import skip

from django.contrib.auth.models import Group, User
from django.utils import timezone

from content.models.content import Content
from events.models import Activity, Event
from jobs.models import Job
from myapa.models.contact import Contact
from myapa.models.contact_relationship import ContactRelationship
from pages.models import LandingPage
from planning.global_test_case import GlobalTestCase
from registrations.forms import *
from store.models import *


@skip
class AddToCartTestCase(GlobalTestCase):
    def setUp(self):
        """
        :meth:`events.models.Event.save` sets a default parent landing page
        which will cause errors here if it doesn't exist (i.e. in a fresh test database)
        """
        event_landing_page, event_landing_page_exists = LandingPage.objects.get_or_create(
            title='Test Page for Conferences & Meetings'
        )
        if not event_landing_page_exists:
            event_landing_page.publish()
        self.parent_landing_master_id = event_landing_page.master_id

    def test_organization_purchase(self):
        org_contact, oc = Contact.objects.get_or_create(
            contact_type='ORGANIZATION',
            company='new planning co.'
        )
        org_user, org_user_created = User.objects.get_or_create(
            first_name='I am the',
            last_name='org user',
            username='325061',
            password='org_pass'
        )
        org_user.contact = org_contact
        org_user.save()
        org_contact.user = org_user
        org_contact.save()

        admin_user, auc = User.objects.get_or_create(
            first_name='I am the',
            last_name='org admin',
            username='325062',
            password='admin_pass'
        )
        admin_contact, adco = Contact.objects.get_or_create(
            contact_type='INDIVIDUAL',
            company='new planning co.'
        )
        admin_user.contact = admin_contact
        admin_user.save()
        admin_contact.user = admin_user
        admin_contact.save()

        con_rel, cr = ContactRelationship.objects.get_or_create(
            source=org_user.contact,
            target=admin_user.contact,
            relationship_type='ADMINISTRATOR'
        )

        comm_con, comm_con_created = Content.objects.get_or_create(
            title='a commissioner organizational subscription'
        )
        comm_pr, comm_pr_created = Product.objects.get_or_create(
            code="COMM",
            publish_status='DRAFT',
            content=comm_con,
            product_type='PRODUCT'
        )

        comm_price, comm_price_created = ProductPrice.objects.get_or_create(
            product=comm_pr,
            price=150.00,
            priority=0,
            title='bundle of 10'
        )

        purchase = comm_pr.add_to_cart(user=org_user)
        self.assertEqual(purchase.product_price.price, Decimal('150.00'))

    def test_product_codes_membership(self):
        mem_con, mem_con_created = Content.objects.get_or_create(title='membership_content')
        mem_pr, mem_pr_created = Product.objects.get_or_create(
            content=mem_con,
            code="MEMBERSHIP_MEM",
            product_type='PRODUCT'
        )

        # invalid_price, inv_pri_created = ProductPrice.objects.get_or_create(title='invalid price', product=mem_pr, price=0.01, priority=1, code='NOMATCH')

        membership_price, mem_pri_created = ProductPrice.objects.get_or_create(
            title='price for membership',
            product=mem_pr,
            price=160.00,
            priority=2,
            code='A'
        )

        self.test_user.groups.remove(self.mem_grp)
        self.test_user.contact.country = "United States"
        self.test_user.contact.salary_range = 'A'
        self.test_user.contact.save()
        self.test_user.save()

        purchase = mem_pr.add_to_cart(user=self.test_user)
        # self.assertNotEqual(purchase.product_price.price, Decimal('0.01'))
        self.assertEqual(purchase.product_price.price, Decimal('160.00'))

    def test_product_codes_student_membership(self):
        stu_con, stu_con_created = Content.objects.get_or_create(title='stu_membership_content')
        stu_pr, stu_pr_created = Product.objects.get_or_create(
            content=stu_con,
            code="MEMBERSHIP_STU",
            product_type='PRODUCT'
        )

        ProductPrice.objects.get_or_create(product=stu_pr, price=40.00, priority=1, code='AA')
        ProductPrice.objects.get_or_create(product=stu_pr, price=45.00, priority=2, code='BB')
        ProductPrice.objects.get_or_create(product=stu_pr, price=5.00, priority=3, code='K')
        ProductPrice.objects.get_or_create(product=stu_pr, price=10.00, priority=4, code='KK')

        self.test_user.groups.remove(self.mem_grp)
        self.test_user.save()
        self.test_user.contact.country = "United States"
        self.test_user.contact.salary_range = 'K'
        self.test_user.contact.save()
        purchase = stu_pr.add_to_cart(user=self.test_user)
        self.assertEqual(purchase.product_price.price, Decimal('5.00'))

        self.test_user.contact.country = "England"
        self.test_user.contact.salary_range = 'KK'
        self.test_user.contact.save()
        purchase = stu_pr.add_to_cart(user=self.test_user)
        self.assertEqual(purchase.product_price.price, Decimal('10.00'))
        # Now non-U.S.(BB)
        self.test_user.contact.salary_range = 'BB'
        self.test_user.contact.country = 'Brazil'
        self.test_user.contact.save()
        purchase = stu_pr.add_to_cart(user=self.test_user)
        self.assertEqual(purchase.product_price.price, Decimal('45.00'))
        # Now non-U.S.(AA)
        self.test_user.contact.salary_range = 'AA'
        self.test_user.contact.country = "Lithuania"
        self.test_user.contact.save()
        purchase = stu_pr.add_to_cart(user=self.test_user)
        self.assertEqual(purchase.product_price.price, Decimal('40.00'))

    def test_product_codes_chapter_membership(self):
        chap_con, chap_con_created = Content.objects.get_or_create(title='chap_membership_content')
        chap_pr, chap_pr_created = Product.objects.get_or_create(
            code="CHAPT_CO",
            publish_status='DRAFT',
            product_type="CHAPTER",
            content=chap_con
        )

        chap_us_stu_price, chap_us_stu_created = ProductPrice.objects.get_or_create(
            product=chap_pr,
            price=10.00,
            priority=0,
            code='K'
        )

        chap_int_stu_price, chap_int_stu_created = ProductPrice.objects.get_or_create(
            product=chap_pr,
            price=18.00,
            priority=1,
            code='KK'
        )

        chap_d_price, chap_d_created = ProductPrice.objects.get_or_create(
            product=chap_pr,
            price=55.00,
            priority=2,
            code='D'
        )

        chap_e_price, chap_e_created = ProductPrice.objects.get_or_create(
            product=chap_pr,
            price=61.00,
            priority=3,
            code='E'
        )

        self.test_user.contact.country = "United States"
        # ecp types no longer are supported in the pricing logic
        # student types are encompassed in the salary ranges
        # K = US STUDENT MEMBER, KK = INT STUDENT MEMBER
        self.test_user.contact.salary_range = 'K'
        self.test_user.contact.save()
        purchase = chap_pr.add_to_cart(user=self.test_user)
        self.assertEqual(purchase.product_price.price, Decimal('10.00'))

        self.test_user.contact.salary_range = 'KK'
        self.test_user.contact.save()
        purchase = chap_pr.add_to_cart(user=self.test_user)
        self.assertEqual(purchase.product_price.price, Decimal('18.00'))

        self.test_user.contact.salary_range = 'D'
        self.test_user.contact.save()
        purchase = chap_pr.add_to_cart(user=self.test_user)
        self.assertEqual(purchase.product_price.price, Decimal('55.00'))

        self.test_user.contact.salary_range = 'E'
        self.test_user.contact.save()
        purchase = chap_pr.add_to_cart(user=self.test_user)
        self.assertEqual(purchase.product_price.price, Decimal('61.00'))

        # Now no ECP and product.code is not on list - price is based on groups (lifemember, member, retiredmember)
        # Chapter not on the ecp-available list - (only ecp product prices will have codes)

        chap2_con, chap2_con_created = Content.objects.get_or_create(
            title='chap2_membership_content'
        )
        chap2_pr, chap2_pr_created = Product.objects.get_or_create(
            code="CHAPT_99",
            publish_status='DRAFT',
            product_type="CHAPTER",
            content=chap2_con
        )

        chap_mem_price, chap_mem_created = ProductPrice.objects.get_or_create(
            product=chap2_pr,
            price=60.00,
            priority=0
        )
        chap_mem_price.required_groups.add(self.mem_grp)
        chap_mem_price.save()

        self.test_user.groups.add(self.mem_grp)
        self.test_user.save()

        purchase = chap2_pr.add_to_cart(user=self.test_user)
        self.assertEqual(purchase.product_price.price, Decimal('60.00'))
        # Nonmember user cannot order a Chapter product if it's not on the "salary range" list
        # Logic loophole: (but if it is they can order if they have a salary range value even if not a member.)
        # this ust tests the normative case:
        self.test_user.groups.remove(self.mem_grp)
        self.test_user.save()
        gp_ret_val = chap2_pr.get_price(self.test_user, self.test_user.contact)
        self.assertEqual(gp_ret_val, None)

    @skip('Test erroring')
    def test_product_codes_job_ad(self):
        # create product and prices                                                                                                                                                   
        job_con, jcc = Job.objects.get_or_create(
            code="JOB_AD",
            publish_status="PUBLISHED"
        )
        job_con.job_type = "PROFESSIONAL_2_WEEKS"
        job_con.save()

        job_pr, job_pr_created = Product.objects.get_or_create(
            code="JOB_AD",
            publish_status='PUBLISHED',
            content=job_con,
            product_type='PRODUCT'
        )

        job_price1, jpc1 = ProductPrice.objects.get_or_create(
            product=job_pr,
            price=250.00,
            priority=3,
            code='PROFESSIONAL_4_WEEKS',
            title='Job Ad - Professional - 4 weeks online'
        )

        job_price2, jpc2 = ProductPrice.objects.get_or_create(
            product=job_pr,
            price=195.00,
            priority=2,
            code='PROFESSIONAL_2_WEEKS',
            title='Job Ad - Professional - 2 weeks online'
        )

        job_price3, jpc3 = ProductPrice.objects.get_or_create(
            product=job_pr,
            price=50.00,
            priority=1,
            code='ENTRY_LEVEL',
            title='Job Ad - Entry Level - 4 weeks online'
        )

        job_price4, jpc4 = ProductPrice.objects.get_or_create(
            product=job_pr,
            price=0.00,
            priority=0,
            code='INTERN',
            title='Job Ad - Internship'
        )

        job_product = job_pr
        job_ad_price = job_product.get_price(user=self.test_user, code=job_con.job_type)
        job_purchase = Purchase.objects.get_or_create(
            user=self.test_user,
            product=job_product,
            product_price=job_ad_price,
            amount=job_ad_price.price,
            submitted_product_price_amount=job_ad_price.price,
            content_master=job_con.master
        )

        self.assertEqual(job_purchase[0].product_price.price, Decimal('195.00'))

    def test_product_codes_pas_subscription(self):
        pass

    def test_sale(self):
        sale_con, sale_con_created = Content.objects.get_or_create(title='sale_membership_content')
        sale_pr, sale_pr_created = Product.objects.get_or_create(
            publish_status='DRAFT',
            content=sale_con,
            product_type='PRODUCT'
        )

        sale_price, s_created = ProductPrice.objects.get_or_create(
            product=sale_pr,
            price=24.95,
            priority=0
        )

        list_price, l_created = ProductPrice.objects.get_or_create(
            product=sale_pr,
            price=34.95,
            priority=1
        )

        nowsies = timezone.now()
        week = timedelta(days=7)
        beg = nowsies - week
        end = nowsies + week
        sale_price.begin_time = beg
        sale_price.end_time = end
        sale_price.save()
        purchase = sale_pr.add_to_cart(user=self.test_user)
        self.assertEqual(purchase.product_price.price, Decimal('24.95'))

        beg = nowsies - (2 * week)
        end = nowsies - week
        sale_price.begin_time = beg
        sale_price.end_time = end
        sale_price.save()
        purchase = sale_pr.add_to_cart(user=self.test_user)
        self.assertEqual(purchase.product_price.price, Decimal('34.95'))

    def test_required_groups(self):
        # Set up a dummy product with member and nonmember prices
        pc, pc_created = Content.objects.get_or_create(
            title='product_content',
            content_type='PUBLICATION'
        )
        tp, tp_created = Product.objects.get_or_create(
            title='test_product',
            code='BOOK_Z00000',
            content=pc,
            product_type='PRODUCT'
        )

        # may need this in all cases because records are persisting in dev database even after 
        # test database is destroyed.
        # if len(tp.prices.all()) > 0:
        #     tp.delete()

        tp.save()
        lp, lp_created = ProductPrice.objects.get_or_create(
            title='list_price',
            product=tp,
            price=34.95,
            priority=2
        )

        mp, mp_created = ProductPrice.objects.get_or_create(
            title='apa_member_price',
            product=tp,
            price=24.95,
            priority=1
        )

        mp.required_groups.add(self.mem_grp)
        mp.save()
        test_product = tp
        # first order as nonmember
        self.test_user.groups.remove(self.mem_grp)
        self.test_user.save()
        purchase = test_product.add_to_cart(user=self.test_user)
        self.assertEqual(purchase.product_price.price, Decimal('34.95'))
        # then order as member
        self.test_user.groups.add(self.mem_grp)
        self.test_user.save()
        purchase = test_product.add_to_cart(user=self.test_user)
        self.assertEqual(purchase.product_price.price, Decimal('24.95'))
        # future groups: nonmember gets member rate for conference when the membership is in the cart
        mem_con, mem_con_created = Content.objects.get_or_create(title='a regular membership')
        conf_con, conf_con_created = Content.objects.get_or_create(
            title='a national conference'
        )
        mem_pr, mem_pr_created = Product.objects.get_or_create(
            code="MEMBERSHIP_MEM",
            publish_status='DRAFT',
            content=mem_con,
            product_type='PRODUCT'
        )
        conf_pr, conf_pr_created = Product.objects.get_or_create(
            code="CONF",
            publish_status='DRAFT',
            content=conf_con,
            product_type='PRODUCT'
        )
        conf_full_opt, cfo_created = ProductOption.objects.get_or_create(
            code='M001',
            publish_status='DRAFT',
            product=conf_pr
        )

        # create prices
        mem_price, m_created = ProductPrice.objects.get_or_create(
            product=mem_pr,
            price=245.00,
            priority=4
        )

        conf_price, c_created = ProductPrice.objects.get_or_create(
            product=conf_pr,
            price=785.00,
            priority=9
        )
        # conf_price.required_groups.add(mem_grp) # uncomment to check required groups for conference... or could use this below as a test for code= ...

        self.mem_grp.products_future.add(mem_pr)
        self.mem_grp.save()
        self.test_user.contact.country = 'United States'
        self.test_user.contact.salary_range = 'E'
        self.test_user.contact.save()
        pur1 = mem_pr.add_to_cart(self.test_user)
        pur2 = conf_pr.add_to_cart(self.test_user, option=conf_full_opt)
        self.assertEqual(pur2.product_price.price, Decimal('785.00'))

    @skip('Test erroring')
    def test_discount_code(self):
        e, ec = Event.objects.get_or_create(
            code='CONF',
            publish_status='DRAFT',
            parent_landing_master_id=self.parent_landing_master_id
        )
        conf_con, conf_con_created = Content.objects.get_or_create(title='a national conference')
        # conf_con.event = e
        # conf_con.event.save()
        conf_pr, conf_pr_created = Product.objects.get_or_create(
            code="CONF",
            publish_status='DRAFT',
            content=conf_con,
            product_type='PRODUCT'
        )
        conf_full_opt, conf_opt_created = ProductOption.objects.get_or_create(
            code='M001',
            publish_status='DRAFT',
            product=conf_pr
        )
        conf_price, conf_price_created = ProductPrice.objects.get_or_create(
            product=conf_pr,
            price=00.00,
            priority=0,
            code='CAICP',
            option_code='M001'
        )

        comp_reg = RegistrationOptionForm(event=e, product=conf_pr, user=self.test_user, code='CAICP')
        comp_pur = comp_reg.save()
        self.assertEqual(comp_pur.product_price.price, Decimal('00.00'))

    def test_option_code(self):
        # test case: ordering a discounted full registration to conference:                                                                                                              
        mem_con, sale_con_created = Content.objects.get_or_create(title='a regular membership')
        conf_con, sale_con_created = Content.objects.get_or_create(title='a national conference')
        mem_pr, mem_pr_created = Product.objects.get_or_create(
            code="MEMBERSHIP_MEM",
            publish_status='DRAFT',
            content=mem_con,
            product_type='PRODUCT'
        )
        conf_pr, conf_pr_created = Product.objects.get_or_create(
            code="CONF",
            publish_status='DRAFT',
            content=conf_con,
            product_type='PRODUCT'
        )
        conf_disc_full_opt, cdfo_created = ProductOption.objects.get_or_create(
            code='M002',
            publish_status='DRAFT',
            product=conf_pr
        )
        self.mem_grp.products_future.add(mem_pr)
        self.mem_grp.save()
        # Discount Full Reg Price: required groups are lifemember
        conf_disc_price, cdp_created = ProductPrice.objects.get_or_create(
            title='Discounted Registration',
            product=conf_pr,
            price=145.00,
            priority=0,
            option_code='M002',
            code=None
        )
        mem_price, m_created = ProductPrice.objects.get_or_create(
            product=mem_pr,
            price=245.00,
            priority=4
        )
        conf_price, c_created = ProductPrice.objects.get_or_create(
            product=conf_pr,
            price=785.00,
            priority=9
        )

        lifemem_grp, lmg = Group.objects.get_or_create(name='lifemember')
        conf_disc_price.required_groups.add(lifemem_grp)
        conf_disc_price.save()

        self.test_user.groups.add(lifemem_grp)
        self.test_user.contact.save()

        pur1 = mem_pr.add_to_cart(self.test_user)
        pur2 = conf_pr.add_to_cart(self.test_user, option=conf_disc_full_opt)
        # assert that pur2 price = member full reg price:                                                                                                                                
        self.assertEqual(pur2.product_price.price, Decimal('145.00'))

    @mock.patch('store.models.CustomEventTickets')
    @mock.patch('store.models.Event')
    @mock.patch('store.models.delete_event_tickets')
    def test_other_required_product(self, mock_delete, mock_events, mock_tickets):
        mock_events.objects.filter().first().get_parent_imis_code.return_value = '19CONF'
        mock_tickets.objects = mock.Mock()
        mock_tickets.objects.filter.return_value = []
        # TO DO... move this product setup / publishing to testing setup / fictures????
        conf_con2, con2_created = Event.objects.get_or_create(
            title='another national conference',
            parent_landing_master_id=self.parent_landing_master_id)

        conf_pr2, conf_pr2_created = Product.objects.get_or_create(
            code="EVENT_CONF2",
            publish_status='DRAFT',
            content=conf_con2,
            product_type='EVENT_REGISTRATION')
        conf_full_opt, co_created = ProductOption.objects.get_or_create(
            code='M001',
            publish_status='DRAFT',
            product=conf_pr2)
        conf_price2, c2_created = ProductPrice.objects.get_or_create(
            product=conf_pr2,
            price=785.00,
            priority=8)

        tour_con, tour_con_created = Activity.objects.get_or_create(
            title='a tour',
            parent_landing_master_id=self.parent_landing_master_id
        )

        tour_pr, tour_pr_created = Product.objects.get_or_create(
            code="CONF2_ACTIVITY_TOUR",
            publish_status='DRAFT',
            content=tour_con,
            product_type='ACTIVITY_TICKET')
        tour_price, tour_price_created = ProductPrice.objects.get_or_create(
            product=tour_pr,
            price=70.00,
            priority=0,
            other_required_product_code='EVENT_CONF2')

        tour_price.other_required_product_must_be_in_cart = False
        tour_price.other_required_option_code = ''
        tour_price.save()

        conf_con2.publish()
        tour_con.publish()

        conf_pr2_published = Product.objects.get(
            publish_status="PUBLISHED",
            code="EVENT_CONF2"
        )

        tour_pr_published = Product.objects.get(
            publish_status="PUBLISHED",
            code="CONF2_ACTIVITY_TOUR"
        )
        conf_full_opt_published = ProductOption.objects.get(
            code="M001",
            publish_status="PUBLISHED",
            product=conf_pr2_published
        )

        # test that get_price() returns None:
        gp_ret_val = tour_pr_published.get_price(self.test_user, self.test_user.contact)
        self.assertEqual(gp_ret_val, None)
        # now add conf first:
        pur4 = conf_pr2_published.add_to_cart(self.test_user, option=conf_full_opt_published)
        pur5 = tour_pr_published.add_to_cart(self.test_user)
        # assert that user got the non-early tour price:
        self.assertEqual(pur5.product_price.price, Decimal('70.00'))

    def test_status(self):
        old_con, old_created = Content.objects.get_or_create(title='inactive national conference')
        old_pr, old_pr_created = Product.objects.get_or_create(
            code="OLD",
            publish_status='DRAFT',
            content=old_con,
            product_type='PRODUCT'
        )
        old_price, op_created = ProductPrice.objects.get_or_create(
            product=old_pr,
            price=385.00,
            priority=0,
            status='I'
        )
        ret_val = old_pr.get_price(self.test_user)
        self.assertEqual(ret_val, None)
