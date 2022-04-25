from django.db import models
from django.contrib.admin.views.main import ChangeList
from django.core import urlresolvers


class SubclassableManager(models.Manager):
    def get_queryset(self):
            return super().get_queryset().filter(**self.model.class_query_args)


class SubclassableModel(models.Model):
    objects = SubclassableManager()
    prevent_auto_class_assignment = False # this prevents a subclass from being auto-applied
    class_query_args = {} # example: {"content_type":"PAGE", "content_area":"MEMBERSHIP"}

    # SOMEWHAT of a hack... but this does work well... see:
    # http://stackoverflow.com/questions/18473850/creating-instances-of-django-proxy-models-from-their-base-class
    # for an example of how this is used to auto-return proxy sub-classes for models
    def get_subclass(self, found_subclass=None):
        found_subclass = found_subclass or type(self)
        # print("===================== CALLING GET SUBCLASS ON: " + str(found_subclass) )

        for subclass in found_subclass.__subclasses__():
            if subclass.prevent_auto_class_assignment:
                class_match = False
            else:
                if subclass.class_query_args:
                    class_match = True # assume innocent until proven guilty
                else:
                    class_match = False # assume guilty until proven innocent
                for key, value in subclass.class_query_args.items():
                    if getattr(self, key, None) != value:
                        class_match = False
                        break
                if class_match:
                    # print("===================== I Matched a: " + str(found_subclass))
                    found_subclass = self.get_subclass(subclass)
        return found_subclass

    def __init__(self, *args, **kwargs):
        # TODO: Shouldn't the ordering of this be reversed?
        # See myapa.tests.contacts.test_models_contact.ContactTestCase.test_set_contact_type_from_imis
        super().__init__(*args, **kwargs)
        self.__class__ = self.get_subclass()

    class Meta:
        abstract = True

    @classmethod
    def get_admin_add_url(cls):
        proxy_model_path = cls.__name__.lower()
        return urlresolvers.reverse("admin:%s_%s_add" % (cls._meta.app_label, proxy_model_path))

    def get_admin_url(self):
        # print("uououououououououououououououououououououououou")
        # print(self.__class__)
        proxy_model_path = self.__class__.__name__.lower()
        return urlresolvers.reverse("admin:%s_%s_change" % (self._meta.app_label, proxy_model_path), args=(self.id,))

    def get_admin_link(self):
        return '<a href="%s">%s</a>' % (self.get_admin_url(), str(self))
    get_admin_link.allow_tags = True
    get_admin_link.short_description="Details"

    def save(self, *args, **kwargs):
        for key, value in self.class_query_args.items():
            setattr(self, key, value)
        super().save(*args, **kwargs)


class SubclassableModelAdminChangeList(ChangeList):
    """
    Used to create a custom url for admin results in order to link to specific admin subclass
    """
    def url_for_result(self, result):
        return result.get_admin_url()


class SubclassableModelAdminMixin(object):
    def get_changelist(self, request, **kwargs):
        return SubclassableModelAdminChangeList

    def get_readonly_fields(self, request, obj=None):
        # TO DO: how to get this for new records?
        if hasattr(super(), "get_readonly_fields"):
            readonly_fields = super().get_readonly_fields(request, obj)
        else:
            readonly_fields = []
        if obj is not None:
            readonly_fields = list(readonly_fields) + list(obj.class_query_args.keys())
        return readonly_fields