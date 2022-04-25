import sys
from os import listdir
from os.path import isfile, join

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission
from django.contrib.sites.models import Site
from django.utils.text import slugify
from django.core.files.images import ImageFile


from wagtail.wagtailcore.models import Page as Wagtail_Page
from wagtail.wagtailcore.models import Site as Wagtail_Site
from wagtail.wagtailcore.models import Collection as WagtailCollection
from wagtail.wagtailcore.models import GroupPagePermission, GroupCollectionPermission
from component_sites.models import ChapterHomePage, DivisionHomePage, ComponentImage, BuildSettings
from component_sites.models import SocialMediaSettings, AppearanceSettings, ProviderSettings

from myapa.models import Contact
from store.models import Product
from directories.models import Directory
from planning.settings import BASE_DIR

env_choices = {
    'L': '-local-development',
    'S': '-staging',
    'P': ''
}

perm_types = ['add', 'edit', 'publish', 'lock']

perm_data = [
    ('Can add document', 252),
    ('Can change document', 252),
    ('Can add image', 250),
    ('Can change image', 250)]



class Command(BaseCommand):
    help = "This command helps to manage Wagtail Microsites creation."
    requires_system_checks = False


    def add_arguments(self, parser):
        parser.add_argument('-s', '--site',
                            type=str,
                            help="Enter the verbose title(s) of the site for action "
                                 "as a comma-seperated list (default:all sites)"
                            )

        parser.add_argument('-e', '--environment',
                            type=str,
                            help="Enter which environment you are creating sites for: "
                                 "Production('P'), Staging('S'), or Local('L')",
                            )

        parser.add_argument('-d', '--delete',
                            action='store_true',
                            help='Delete site(s) instead of creating it.(Note: Does not delete pages.)',
                            )

        parser.add_argument('-l', '--list',
                            action='store_true',
                            help='List all current sites verbose titles in Component Sites file.',
                            )
        parser.add_argument('-a', '--admin',
            action='store_true',
            help='Do Not Use: Used to indicate execution initiated via the admin',
                            )

        parser.add_argument('-t', '--type',
            type=str,
            help="Do Not Use: Enter site type of new site.",
                            )

        parser.add_argument('-u', '--domain',
            type=str,
            help="Do Not Use: Enter domain of new site.",
                            )

        parser.add_argument('-p', '--provider',
                            type=str,
                            help="Do Not Use: Enter providerID of new site.",
                            )

        parser.add_argument('-g', '--group',
            type=str,
            help="Do Not Use: Enter name of Admin Group",
                            )

    def handle(self, *args, **options):
        if options['admin']:
            this_site = WagtailSiteManager({}, options.get('environment'),
                                           title=options.get('site'), domain=options.get('domain'),
                                           site_type=options.get('type'), group=options.get('group'),
                                           provider=options.get('provider'))
            this_site.create_site()
        else:
            self.validate_args(options)
            self.iterate_build_settings(options, delete_site=self.delete_site)

    def validate_args(self, options):
        # Unpacks Sites argument to see if this run is for a single site, a subset or all sites
        self.existing_site_names = [site.site_name for site in Wagtail_Site.objects.all()]

        #List sites argument, executtes list sites which will end this execution
        if options['list']:
            self.list_sites()

        #Environment argument(required)
        if not options['environment'] or options['environment'] not in env_choices:
            raise CommandError("You are required to enter a valid environment, i.e. '-e P/S/L', to run this command.")

        self.delete_site = options['delete']

        # validating site_names if they are given

        self.given_sites = options['site'].split(', ') if options['site'] else None
        if self.given_sites:
            for site_name in self.given_sites:
                if site_name not in self.existing_site_names:
                    raise CommandError("%s is not a valid sitename" % site_name)

        self.env = options['environment']

    def list_sites(self):
        self.stdout.write("Here are all the current site names: ")
        self.stdout.write(", ".join(self.existing_site_names))
        sys.exit()

    def iterate_build_settings(self, options, delete_site = False):
        for site in BuildSettings.objects.filter(env='P'):
            if not self.given_sites or options['site'] in self.given_sites:
                this_site = WagtailSiteManager({}, self.env,
                                   title=site.title, domain=site.domain,
                                   site_type=site.type, group=site.admin_group.name,
                                   provider=site.provider.user.username)
                if delete_site:
                    this_site.delete_wagtail_site()
                else:
                    this_site.create_site()

class WagtailSiteManager:
    root_page = Wagtail_Page.objects.get(title='Root')
    root_coll = WagtailCollection.get_first_root_node()

    component_admin_group = Group.objects.get(name="wagtail-admin")
    wagtail_admin_permission = Permission.objects.get(name='Can access Wagtail admin')

    for arp in Permission.objects.filter(name='Can add redirect'):
        if arp.natural_key()[1] == 'wagtailredirects':
            can_add_redirect = arp

    for crp in Permission.objects.filter(name='Can change redirect'):
        if crp.natural_key()[1] == 'wagtailredirects':
            can_change_redirect = crp

    for drp in Permission.objects.filter(name='Can delete redirect'):
        if drp.natural_key()[1] == 'wagtailredirects':
            can_delete_redirect = drp

    def __init__(self, info, env, title=None, domain=None, site_type=None, group=None, provider=None):
        self.title = title if title else info.get('verbose_name')
        self.site_prefix = domain if domain else info.get('site').split('.')[0]
        self.domain_name = "%s%s.planning.org" % (self.site_prefix, env_choices[env])
        self.group_name = group if group else info.get('admin_group')
        self.provider = provider if provider else info.get('username')
        self.type = site_type if site_type else info.get('type')
        self.port = 8000 if env == 'L' else 80
        self.collection_name = self.title + " " + self.type.title() + " Resources Collection"
        self.info = info
        self.upload = not title

    def create_site(self):
        print(self.domain_name)
        self.create_django_site()
        self.create_wagtail_site()
        self.create_wagtail_collection()
        self.create_wagtail_groups()
        self.update_wagtail_permissions()
        self.convert_site_settings()
        self.upload_files_to_collection()


    def create_django_site(self):
        dj_site, created = Site.objects.get_or_create(name=self.domain_name, domain=self.domain_name)
        if created:
            print("\t- Django site created.")
        else:
            print("\t- Django site existed.")

    def create_wagtail_site(self):
        if self.type == 'CHAPTER':
            self.home_page = ChapterHomePage.objects.filter(title__contains=self.title).first()
            if not self.home_page:
                self.home_page = ChapterHomePage()
                self.home_page.title = "Welcome to APA " + self.title
                self.home_page.slug = slugify(self.home_page.title)
                self.root_page.add_child(instance=self.home_page)
                print("\t- Chapter Home Page created.")
        elif self.type == 'DIVISION':
            self.home_page = DivisionHomePage.objects.filter(title__contains=self.title).first()
            if not self.home_page:
                self.home_page = DivisionHomePage()
                self.home_page.title = "APA " + self.title + " Division"
                self.home_page.slug = slugify(self.home_page.title)
                self.root_page.add_child(instance=self.home_page)
                print("\t- Division Home Page created.")

        self.ws, created = Wagtail_Site.objects.get_or_create(root_page_id=self.home_page.id,
                                                         hostname=self.domain_name, port=self.port)
        if created:
            print("\t- Wagtail Site created.")
            self.ws.site_name = self.domain_name
            self.ws.save()
        else:
            print("\t- Wagtail Site existed.")

    def create_wagtail_collection(self):
        if not WagtailCollection.objects.filter(name=self.collection_name).first():
            self.root_coll.add_child(name=self.collection_name)
            print("\t- %s created." % self.collection_name)
        else:
            print("\t- %s already exists." % self.collection_name)
        self.collection = WagtailCollection.objects.get(name__contains=self.collection_name)

    def create_wagtail_groups(self):
        self.admin_group, admin_group_created = Group.objects.get_or_create(name=self.group_name)
        if admin_group_created:
            print("\t- %s group created." % self.group_name)
        else:
            print("\t- %s group existed." % self.group_name)

    def update_wagtail_permissions(self):
        print("\t- Permissions: ")
        self.admin_group.permissions.clear()
        self.admin_group.permissions.set([self.wagtail_admin_permission,
                                          self.can_add_redirect,
                                          self.can_change_redirect,
                                          self.can_delete_redirect
                                          ])
        self.component_admin_group.permissions.set([self.wagtail_admin_permission,
                                                    self.can_add_redirect,
                                                    self.can_change_redirect,
                                                    self.can_delete_redirect
                                                    ])


        for ptype in perm_types:
            GroupPagePermission.objects.get_or_create(group=self.component_admin_group, permission_type=ptype,
                                                      page=self.home_page)
            GroupPagePermission.objects.get_or_create(group=self.admin_group, permission_type=ptype,
                                                      page=self.home_page)

            for child in self.home_page.get_children():
                GroupPagePermission.objects.get_or_create(group=self.admin_group, permission_type=ptype, page=child)
        print("\t\t-GroupPage permissions updated.")


        for perm in perm_data:
            permission = Permission.objects.filter(
                name=perm[0],
                content_type=perm[1]
            ).first()
            GroupCollectionPermission.objects.get_or_create(
                collection=self.collection,
                group=self.component_admin_group,
                permission=permission
            )
            GroupCollectionPermission.objects.get_or_create(
                collection=self.collection,
                group=self.admin_group,
                permission=permission
            )
        print("\t\t-Collection permissions updated.")

    def delete_wagtail_site(self):
        ws = Wagtail_Site.objects.filter(hostname=self.domain_name).first()
        if ws:
            ws.delete()
            print("Wagtail site for %s was deleted." % self.domain_name)
        else:
            print("Wagtail site for %s was not deleted because it doesn't exist." % self.domain_name)

    def upload_files_to_collection(self):
        if self.upload:
            #building static file folder dir
            if 'static' in self.info:
                image_dir = BASE_DIR + "/component_sites/static/component-sites/image/" + self.info['static']
            else:
                image_dir = BASE_DIR+"/component_sites/static/component-sites/image/"+ self.title.replace(' ', '').lower()

            for file_name in listdir(image_dir):
                file_path = join(image_dir, file_name)
                if isfile(file_path):
                    if file_path.split('.')[-1] in ['gif', 'jpeg', 'png', 'jpg']:
                        with open(file_path, 'rb') as f:
                            i = ImageFile(f, name=file_name )
                            if 'horizontal' in file_path:
                                title = self.title.replace(' ', '')+"WideLogo"
                                hor_wt_image = ComponentImage(title=title, file=i)
                                hor_wt_image.collection = self.collection
                                if not ComponentImage.objects.filter(title=title):
                                    hor_wt_image.save()
                                    self.ws.appearancesettings.logo_wide = hor_wt_image
                                    print("\t\t\tCreated and Attributed %s." % title)
                                else:
                                    img = ComponentImage.objects.get(title=title)
                                    self.ws.appearancesettings.logo_wide = img
                                    print("\t\t\t%s exists." % title)
                            else:
                                sm_wt_image = ComponentImage(file=i)
                                sm_wt_image.collection = self.collection
                                title = self.title.replace(' ', '')+ "SmallLogo"
                                if not ComponentImage.objects.filter(title=title):
                                    sm_wt_image.title = title
                                    sm_wt_image.save()
                                    self.ws.appearancesettings.logo_small = sm_wt_image
                                    self.ws.socialmediasettings.default_og_image = sm_wt_image
                                    print("\t\t\tCreated and Attributed %s" % title)
                                else:
                                    img = ComponentImage.objects.get(title=title)
                                    self.ws.appearancesettings.logo_small = img
                                    self.ws.socialmediasettings.default_og_image = img
                                    print("\t\t\t%s exists." % title)
                            self.ws.appearancesettings.save()
                            self.ws.socialmediasettings.save()

    def convert_site_settings(self):
        #SocialMedia
        soc_settings, created = SocialMediaSettings.objects.get_or_create(site=self.ws)
        if created:
            print("\t-New Social Media Settings created:")
        else:
            print("\t-Social Media Settings updated:")

        if self.info:
            soc_settings.facebook = self.info.get('facebook')
            soc_settings.youtube = self.info.get('youtube')
            soc_settings.twitter = self.info.get('twitter')
            soc_settings.instagram = self.info.get('instagram')
            soc_settings.linkedin = self.info.get('linkedin')
            soc_settings.save()

        #AppearanceSettings
        rgb = tuple(self.info['color'].split(',')) if self.info else ('22', '87', '136')
        hex = '#%02x%02x%02x' % (int(rgb[0]), int(rgb[1]), int(rgb[2]))
        app_settings, created = AppearanceSettings.objects.get_or_create(site=self.ws)
        app_settings.color = hex
        if created:
            print("\t-New Appearance Settings created:")
        else:
            print("\t-Appearance Settings updated:")

        app_settings.save()

        #ProviderSettings
        prov_settings, created = ProviderSettings.objects.get_or_create(site=self.ws)

        if created:
            print("\t-New Provider Settings created:")
        else:
            print("\t-Provider Settings updated:")

        contact = Contact.objects.get(user__username=self.provider)
        prov_settings.contact = contact
        print("\t\t\t Contact %s Added" % contact)
        try:
            job_product = Product.objects.get(code=self.info['jobs_product_code'], publish_status='PUBLISHED')
            prov_settings.job_product = job_product
            print("\t\t\t Job Product %s Added" % contact)
        except:
            print("\t\t\t There was no job product for", self.title)

        prov_settings.jobs_post_instruction_code = self.info.get('job_post_instruction_code')
        prov_settings.jobs_submission_category_code = self.info.get('job_submission_category_code')

        try:
            directory = Directory.objects.get(code=self.info['directory_code'])
            prov_settings.directory = directory
            print("\t\t\t Directory %s Added" % contact)
        except:
            print("\t\t\t There was no directory given for", self.title)

        try:
            tag = Tag.objects.get(code=self.info['tag_code'], tag_type__title='Division')
            prov_settings.tag = tag
            print("\t\t\t Division Tag %s Added" % contact)
        except:
            print("\t\t\t There was no Division Tag for", self.title)
        prov_settings.save()








