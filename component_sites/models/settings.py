from colorful.fields import RGBColorField

from wagtail.contrib.settings.models import BaseSetting, register_setting

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import Group

from wagtail.wagtailadmin.edit_handlers import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel

from myapa.models import Contact
envs = [
    ('L', 'Local'),
    ('S', 'Staging'),
    ('P', 'Production')
    ]

site_types = [('CHAPTER', 'Chapter'),
              ('DIVISION', 'Division')]

class BuildSettings(models.Model):
    class Meta:
        verbose_name_plural = "Build Settings"

    title = models.CharField(max_length=100, blank=False, null=False)
    domain = models.CharField(max_length=100, blank=False, null=False)
    env = models.CharField(max_length=1, choices=envs, default='P')
    type = models.CharField(max_length=30, choices=site_types)
    admin_group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, help_text="Group for Site Admins")
    provider = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, help_text="CM Provider and Site owner",
                                 limit_choices_to=Q(member_type="CHP") | Q(member_type="DVN") )

    def __str__(self):
        ##way to get the reverse of choices. There has to be a better way
        verbose_env = [item[1] for item in envs if self.env == item[0]][0]
        return "%s %s" % (self.title, verbose_env)

@register_setting
class SocialMediaSettings(BaseSetting):
    facebook = models.CharField(
        max_length=255, help_text='Your Facebook page partial URL', null=True, blank=True)
    youtube = models.CharField(
        max_length=255, help_text='Your YouTube channel or user account partial URL', null=True, blank=True)
    twitter = models.CharField(
        max_length=255, help_text='Your Twitter username, without the @', null=True, blank=True)
    instagram = models.CharField(
        max_length=255, help_text='Your Instagram username, without the @', null=True, blank=True)
    linkedin = models.CharField(
        max_length=255, help_text='Your LinkedIn page partial URL', null=True, blank=True)
    default_og_image = models.ForeignKey('component_sites.ComponentImage', null=True, blank=True, on_delete=models.SET_NULL,
                                   help_text="default OG image for pages with no assigned og image. Should be logo with recommended size 1200x630px", related_name='+'
                                   )

    panels = [
        FieldRowPanel([
                FieldPanel("facebook"),FieldPanel("instagram"),
                ]),
        FieldRowPanel([FieldPanel("youtube"), FieldPanel("twitter")]),
        FieldRowPanel([FieldPanel("linkedin")],),
        ImageChooserPanel("default_og_image"),
    ]

@register_setting
class AppearanceSettings(BaseSetting):
    logo_small = models.ForeignKey('component_sites.ComponentImage', null=True, blank=True, on_delete=models.SET_NULL,
        help_text="This logo is used for small viewport and favicon", related_name='+'
    )
    logo_wide = models.ForeignKey('component_sites.ComponentImage', null=True, blank=True, on_delete=models.SET_NULL,
        help_text="This wide logo is for the large viewport header", related_name='+'
    )

    color = RGBColorField(default="#165788")

    def rgb_string(self):
        if self.color:
            return "%s, %s, %s" % (int(self.color[1:3],16),int(self.color[3:5],16), int(self.color[5:7],16))

    panels = [
        ImageChooserPanel("logo_small") ,
        ImageChooserPanel("logo_wide"),
        FieldPanel("color"),
        ]

@register_setting
class ProviderSettings(BaseSetting):
    contact = models.ForeignKey('myapa.Contact', related_name='site', on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to=Q(member_type="CHP") | Q(member_type="DVN"))
    additional_contacts = models.ManyToManyField('myapa.Contact', verbose_name = "Sections", null=True, blank=True, limit_choices_to=Q(contact_type="ORGANIZATION") & Q(company__icontains="Section"))
    job_product = models.ForeignKey('store.Product', on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to=Q(code__icontains='JOB_AD_') & Q(publish_status='PUBLISHED'))

    jobs_post_instruction_code = models.CharField(
        max_length=255, help_text='Job Instructions Code', null=True, blank=True)

    jobs_submission_category_code = models.CharField(
        max_length=255, help_text='Job Submission Code', null=True, blank=True)

    directory = models.ForeignKey('directories.Directory', on_delete=models.SET_NULL, null=True, blank=True)

    tag = models.ForeignKey('content.tag', on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to=Q(tag_type__title='Division'))

    panels = [
        MultiFieldPanel([
            FieldPanel("contact"),
            FieldPanel("additional_contacts"),], heading="Contacts"),
        MultiFieldPanel([
            FieldRowPanel([FieldPanel("job_product"),]),
            FieldRowPanel([FieldPanel("jobs_post_instruction_code"), FieldPanel("jobs_submission_category_code"),]),],
            heading='Jobs'),
        MultiFieldPanel([FieldRowPanel([FieldPanel("directory"), FieldPanel("tag")])], heading='Other Related Objects'),
    ]


