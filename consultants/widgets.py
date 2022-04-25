from django.forms.widgets import ClearableFileInput, CheckboxInput
from django.utils.translation import ugettext_lazy
from django.utils.html import conditional_escape, format_html
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe


class NewTabClearableFileInput(ClearableFileInput):
    initial_text = ugettext_lazy('Currently')
    input_text = ugettext_lazy('Change Image')
    clear_checkbox_label = ugettext_lazy('Clear Image')
    template_with_initial = (
        '%(initial_text)s: <a href="%(initial_url)s">%(initial)s</a> <br /><br />'
        # '%(clear_template)s<br />%(input_text)s: %(input)s'
        '%(clear_template)s%(input_text)s: %(input)s'
    )
    # template_with_clear = '%(clear)s <label for="%(clear_checkbox_id)s">%(clear_checkbox_label)s</label>'
    template_with_clear = '%(clear_checkbox_label)s: %(clear)s <br /><br />'

    url_markup_template = '<a href="{0}" target="_blank">{1}</a>'

    def __init__(self, attrs=None):
        # super(NewTabClearableFileInput, self).__init__(attrs)

        super().__init__(attrs)

    def render(self, name, value, attrs=None):
        # self is custom widget object
        # name is name of field widget belongs to
        # value is the file uploaded to the field
        substitutions = {
            'initial_text': self.initial_text,
            'input_text': self.input_text,
            # add
            'clear_template': '',
            'clear_checkbox_label': self.clear_checkbox_label,

        }
        template = '%(input)s'
        substitutions['input'] = super(ClearableFileInput, self).render(name, value, attrs)

        if value and hasattr(value, "url"):
            template = self.template_with_initial
            substitutions.update(self.get_template_substitution_values(value))
            substitutions['initial'] = format_html(self.url_markup_template,
                                               value.url,
                                               force_text(value))
            if not self.is_required:
                checkbox_name = self.clear_checkbox_name(name)
                checkbox_id = self.clear_checkbox_id(checkbox_name)
                substitutions['clear_checkbox_name'] = conditional_escape(checkbox_name)
                substitutions['clear_checkbox_id'] = conditional_escape(checkbox_id)
                substitutions['clear'] = CheckboxInput().render(checkbox_name, False, attrs={'id': checkbox_id})
                substitutions['clear_template'] = self.template_with_clear % substitutions

        return mark_safe(template % substitutions)

    # THIS BREAKS THE WIDGET FUNCTIONING:
    # def value_from_datadict(self, data, files, name):
    #     checkbox_val = CheckboxInput().value_from_datadict(
    #             data, files, self.clear_checkbox_name(name))
    #     print("CHECKBOX VALUE IS ------ ", checkbox_val)
    #     super(NewTabClearableFileInput, self).value_from_datadict(data, files, name)
