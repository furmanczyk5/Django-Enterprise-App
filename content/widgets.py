import datetime

from django.utils.dates import MONTHS
from django import forms
from django.forms import widgets
from django.forms.utils import flatatt
from django.utils.safestring import mark_safe
from django.utils.html import format_html


class SelectFacade(forms.Select):

    def __init__(self, attrs=None, choices=(), facade_attrs={}, pretext="", posttext="", use_required_attribute=True):
        super().__init__(attrs, choices)

        self.facade_attrs = facade_attrs
        self.pretext = pretext
        self.posttext = posttext
        self.use_html_required = use_required_attribute

    def use_required_attribute(self, initial):
        # Don't use the 'required' attribute because browser validation would
        # always require this, even when there is no state option available for
        # a given country, like Cayman Islands
        return self.use_html_required

    def render(self, name, value, attrs=None):

        self.facade_attrs["class"] = self.facade_attrs.get("class", "")
        self.facade_attrs["class"] += " select-facade"
        final_facade_attrs = self.facade_attrs # self.build_attrs(self.facade_attrs)

        output = [format_html('<span{0}>', flatatt(final_facade_attrs))]
        output.append(self.pretext)
        output.append("<span class='facade-text'></span>")
        output.append(self.posttext)

        select_input_html = super().render(name, value, attrs)
        output.append(select_input_html)

        output.append('</span>')

        return mark_safe('\n'.join(output))


class CheckboxFacade(forms.CheckboxInput):

    def __init__(self, attrs=None, facade_attrs={}):
        super().__init__(attrs)

        self.facade_attrs = facade_attrs

    def render(self, name, value, attrs=None):

        self.facade_attrs["class"] = self.facade_attrs.get("class", "")
        self.facade_attrs["class"] += " checkbox-facade"
        final_facade_attrs = self.build_attrs(self.facade_attrs)
        output = [format_html('<a{0}>', flatatt(final_facade_attrs))]

        checkbox_input_html = super().render(name, value, attrs)
        output.append(checkbox_input_html)

        output.append(self.facade_attrs.get("label", ""))
        output.append('</a>')

        return mark_safe('\n'.join(output))


class DatetimeFacade(forms.TextInput):

    def __init__(self, attrs=None, facade_attrs={}):
        super().__init__(attrs)

        facade_attrs["class"] = facade_attrs.get("class", "")
        facade_attrs["class"] += " datetime-facade"
        self.final_facade_attrs = self.build_attrs(facade_attrs)

    def render(self, name, value, attrs=None):

        output = [format_html('<span{0}>', flatatt(self.final_facade_attrs))]

        if not attrs:
            attrs = {}

        attrs["class"] = self.attrs.get("class", "")
        attrs["class"] += " planning-datetime-widget"

        input_html = super().render(name, value, attrs)

        output.append(input_html)

        output.append('</span>')

        return mark_safe('\n'.join(output))


class YearMonthDaySelectorWidget(widgets.MultiWidget):

    def __init__(self, attrs=None, **kwargs):

        self.include_day = kwargs.get("include_day", True)
        self.include_month = kwargs.get("include_month", True)
        self.min_year = kwargs.get("min_year", 1899)
        self.max_year = kwargs.get("max_year", datetime.datetime.today().year)
        self.year_sort = kwargs.get("year_sort", "desc") # or asc
        self.us_notation = kwargs.get("us_notation", True)  # MONTH DAY YEAR FORMAT
        self.numbered_months = kwargs.get("numbered_months", False)  # SPELLED OUT MONTHS (FEBUARY VS 2)
        self.optional_day = kwargs.get("optional_day", False)  # allow user to optionally leave out day
        self.optional_month = kwargs.get("optional_month", False)  # allow user to optionally leave out month

        if self.year_sort == "asc":
            years = [(None, "Select a Year")] + [(year, year) for year in range(self.min_year, self.max_year, 1)]
        else:
            years = [(None, "Select a Year")] + [(year, year) for year in range(self.max_year, self.min_year, -1)]

        if self.include_month and self.numbered_months:
            months = [(None, "Select a Month")] + [(i, i) for i in range(1,13)]
        elif self.include_month:
            months = [(None, "Select a Month")] + [(m, str(MONTHS[m])) for m in range(1,13)]

        if self.include_day:
            days = [(None, "Select a Day")] + [(day, day) for day in range(1, 32, 1)]

        _widgets = [
            SelectFacade(attrs=attrs, facade_attrs={"data-empty-text":"Year", "class":"margin-right"}, choices=years),
        ]

        if self.include_month:
            _widgets.append(SelectFacade(attrs=attrs, facade_attrs={"data-empty-text":"Month", "class":"margin-right"}, choices=months)),

        if self.include_month and self.include_day:
            _widgets.append(SelectFacade(attrs=attrs, facade_attrs={"data-empty-text":"Day"}, choices=days) )

        super().__init__(_widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.year, value.month, value.day]
        else:
            return [None, None, None]

    def format_output(self, rendered_widgets):
        if self.us_notation:
            ordered_widgets = [rendered_widgets[0]]

            if self.include_month:
                ordered_widgets.insert(0, rendered_widgets[1])

            if self.include_month and self.include_day:
                ordered_widgets.insert(1, rendered_widgets[2])

            return ''.join(ordered_widgets)
        else:
            return ''.join(rendered_widgets)

    def value_from_datadict(self, data, files, name):
        datelist = [
            widget.value_from_datadict(data, files, name + '_%s' % i)
            for i, widget in enumerate(self.widgets)]
        try:
            year = int(datelist[0])

            if (not self.include_month) or (self.optional_month and not datelist[1]):
                month = 1
            else:
                month = int(datelist[1])

            if not self.include_month or not self.include_day or (self.optional_day and not datelist[2]):
                day = 1
            else:
                day = int(datelist[2])

            D = datetime.datetime(
                year=year,
                month=month,
                day=day,
            )

        except Exception as e:
            return ''
        else:
            return D


# class TagCheckboxChoiceInput(widgets.CheckboxChoiceInput):

#     def render(self, name=None, value=None, attrs=None):
#         if self.id_for_label:
#             label_for = format_html(' for="{}"', self.id_for_label)
#         else:
#             label_for = ''
#         attrs = dict(self.attrs, **attrs) if attrs else self.attrs
#         return format_html(
#             '<span class="tag-checkbox"><label{}>{}<a class="btn btn-sm btn-dark btn-facet-tag-selected">{} <span class="icon-apa-close"></span></a></label></span>', label_for, self.tag(attrs), self.choice_label
#         )


# class TagCheckboxFieldRenderer(widgets.CheckboxFieldRenderer):
#     choice_input_class = TagCheckboxChoiceInput


class TagCheckboxSelectMultiple(widgets.CheckboxSelectMultiple):
    option_template_name = "content/newtheme/widgets/checkbox-option.html"


class SelectMultipleTagsWidget(widgets.MultiWidget):
    """
    select multiple widget. Select from a dropdown of available options,
    the selected options will appear as tags under the dropdown,
    must be used in combo with --.css and --.js files
    """
    template_name = "content/newtheme/widgets/multiple-tags.html"

    def __init__(self, attrs=None, choices=(), **kwargs):

        _widgets = [
            widgets.Select(attrs=attrs, choices=choices),
            TagCheckboxSelectMultiple(attrs=attrs, choices=choices),
        ]

        return super().__init__(_widgets, attrs, **kwargs)

    # def render(self, name, value, attrs=None, renderer=None):
    #     if not value:
    #         value = [ False for x in self.fieldnames ]
    #     rendered_widgets = [ x.render('%s_%d' % (name,i), value[i]) for i,x in enumerate(self.widgets) ]
    #     return super().render(name, rendered_widgets, attrs=None)

    def render(self, name, value, attrs=None):
        if isinstance(value, list):
            value = ",".join(value)  # need to make sure this is comma separated string, or decompress will not be called
        return super().render(name, value, attrs=None)

    def decompress(self, value):
        if value:
            return [None, value.split(",")]
        else:
            return [None, None]

    # TO DO ... a bit of a hack for now... should use widget template instead of format_output
    # def format_output(self, rendered_widgets):
    #     return '<div class="selectmultipletagswidget"><div>{0}</div><div>{1}</div></div>'.format(*rendered_widgets)

    def value_from_datadict(self, data, files, name):
        value_lists = [
            widget.value_from_datadict(data, files, name + '_%s' % i)
            for i, widget in enumerate(self.widgets)]

        try:
            return value_lists[1]
        except:
            return None
