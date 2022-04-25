import datetime

from django import forms

from content.forms import StateCountryModelFormMixin, AddFormControlClassMixin
from content.widgets import SelectFacade, YearMonthDaySelectorWidget
from myapa.forms import JoinCreateAccountForm
from myapa.models.constants import RACE_CHOICES, HISPANIC_ORIGIN_CHOICES, GENDER_CHOICES
from store.models import ProductCart


class NameForm(forms.Form):
  error_css_class = 'has-error'
  required_css_class = 'required'
  name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name'}))
  email = forms.EmailField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
  prefix_name = forms.ChoiceField(required=False,
        widget=forms.Select(attrs={'class':'form-control'}),
        help_text = "Optional",
        choices =( ("", "--"),
                    ("Col.", "Col." ),
                    ("Cpt", "Cpt." ),
                    ("Dr", "Dr."), 
                    ("Hon.", "Hon."),
                    ("Lt", "Lt."),

                    ("Maj", "Maj." ),
                    ("Mr.", "Mr." ),
                    ("Mrs.", "Mrs."), 
                    ("Ms", "Ms."),
                    ("Prof", "Prof."),

                    ("Rev.", "Rev." ),
                    ("Sgt", "Sgt." )
                    )
        )
  birth_date = forms.DateField(label="Date of Birth", required=True, widget=YearMonthDaySelectorWidget() )
  
  race = forms.MultipleChoiceField(
      label="Race", 
      help_text="Please check one or more below", 
      required=True, 
      choices=[("", "I prefer not to answer")] + list(RACE_CHOICES),
      widget=forms.CheckboxSelectMultiple(attrs={'class':'form-control'})
  )
  hispanic_origin = forms.ChoiceField(
      label="Hispanic Origin", 
      help_text="Please select one below", 
      required=True, 
      choices= list(HISPANIC_ORIGIN_CHOICES),
      widget=forms.RadioSelect(attrs={'class':'form-control'})
  )

  gender = forms.ChoiceField(label="Gender", required=True, choices=[(None, "- select -")] + list(GENDER_CHOICES), widget=SelectFacade(attrs={'class':'form-control'}) )



class MyAccountForm1(StateCountryModelFormMixin, forms.Form):
  is_authenticated = False

  prefix_name = forms.ChoiceField(label="Prefix", help_text = "Optional", required=False, widget=forms.Select(attrs={'class':'form-control'}), choices = ( 
                  ("", "--"),
                  ("Col.", "Col." ),
                  ("Cpt", "Cpt." ),
                  ("Dr", "Dr."), 
                  ("Hon.", "Hon."),
                  ("Lt", "Lt."),

                  ("Maj", "Maj." ),
                  ("Mr.", "Mr." ),
                  ("Mrs.", "Mrs."), 
                  ("Ms", "Ms."),
                  ("Prof", "Prof."),

                  ("Rev.", "Rev." ),
                  ("Sgt", "Sgt." )
                  )
  )
  first_name = forms.CharField(label="First Name", required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
  middle_name = forms.CharField(label="Middle Initial", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}), required=False)
  last_name = forms.CharField(label="Last Name", required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
  informal_name = forms.CharField(label="Nickname", help_text="Optional", required=False)
  suffix_name = forms.ChoiceField(help_text="Optional", required=False, choices =(
                  ("", "--"),
                  ("II", "II" ),
                  ("III", "III" ),
                  ("IV", "IV" ),
                  ("Jr.", "Jr."), 
                  ("Sr.", "Sr."))
  )   
  email = forms.EmailField(label="Email", required=True, widget=forms.TextInput(attrs={'placeholder': 'Email'}))
  verify_email = forms.EmailField(label="Verify Email", required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email Verify'}))
  #date_of_birth = forms.DateField(label="Date of Birth", required=True)
  password = forms.CharField(label="Password", required=True, widget=forms.PasswordInput(render_value=True, attrs={'class':'form-control'}))
  verify_password = forms.CharField(label="Verify Password", required=True, widget=forms.PasswordInput(render_value=True, attrs={'class':'form-control'}))
  password_hint = forms.ChoiceField(label = "Password Hint",required = True, widget=forms.Select(attrs={'class':'form-control'}), 
      choices =( ("", "(select a security question)"),
                  ("A", "What is your Mother's Maiden Name?" ),
                  ("B", "What city were you born in?" ),
                  ("C", "What is your pet's name?"), 
                  ("D", "What is your Father's Middle Name?"),
                  ("E", "What is your favorite sports team?")
                  )
      )
  #password_hint = forms.CharField(label="Password Hint", required=False)
  password_answer = forms.CharField(label="Password Hint Answer", required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Password Hint Answer'}))
  # security_questions = forms.CharField(label="Security Question", required=False, initial=False)

  def __init__(self, *args, **kwargs):
    super(MyAccountForm, self).__init__(*args, **kwargs)

    for field in self.fields.values():
        field.error_messages = {'required':'The field {fieldname} is required'.format(fieldname=field.label)}
    for field in iter(self.fields):
        self.fields[field].widget.attrs.update({
            'class': 'form-controlasd'
    })
  def clean(self):

    cleaned_data = super().clean()

    password = cleaned_data.get("password", None)
    verify_password = cleaned_data.get("verify_password", None)

    if password is None or verify_password is None:
        pass
    elif len(password) < 6:
        self.add_error("password", "Your password must be at least 6 characters")
    elif password != verify_password:
        self.add_error("password", "Passwords do not match")


    email = cleaned_data.get("email", None)
    verify_email= cleaned_data.get("verify_email", None)

    if email is None or verify_email is None:
        pass
    elif email != verify_email:
        self.add_error("email", "Email fields do not match")



    return cleaned_data

class MyAccountForm(StateCountryModelFormMixin, forms.Form):
  def __init__(self, *args, **kwargs):
    super(MyAccountForm, self).__init__(*args, **kwargs)

    for field in self.fields.values():
        field.error_messages = {'required':'The field {fieldname} is required'.format(fieldname=field.label)}
    for field in iter(self.fields):
        self.fields[field].widget.attrs.update({
            'class': 'form-control'
    })
  is_authenticated = False

  prefix_name = forms.ChoiceField(label="Prefix", help_text = "Optional", required=False, choices = ( 
                  ("", "--"),
                  ("Col.", "Col." ),
                  ("Cpt", "Cpt." ),
                  ("Dr", "Dr."), 
                  ("Hon.", "Hon."),
                  ("Lt", "Lt."),

                  ("Maj", "Maj." ),
                  ("Mr.", "Mr." ),
                  ("Mrs.", "Mrs."), 
                  ("Ms", "Ms."),
                  ("Prof", "Prof."),

                  ("Rev.", "Rev." ),
                  ("Sgt", "Sgt." )
                  )
  )
  first_name = forms.CharField(label="First Name", help_text="Firstname", required=True)
  middle_name = forms.CharField(label="Middle Initial", widget=forms.TextInput(attrs={'placeholder': 'Optional'}), required=False)
  last_name = forms.CharField(help_text="Last Name", required=True)
  informal_name = forms.CharField(label="Nickname", help_text="Optional", required=False)
  suffix_name = forms.ChoiceField(help_text="Optional", required=False, choices =(
                  ("", "--"),
                  ("II", "II" ),
                  ("III", "III" ),
                  ("IV", "IV" ),
                  ("Jr.", "Jr."), 
                  ("Sr.", "Sr."))
  )   
  email = forms.EmailField(label="Email", required=True)
  verify_email = forms.EmailField(label="Verify Email", required=True)
  #date_of_birth = forms.DateField(label="Date of Birth", required=True)
  password = forms.CharField(label="Password", required=True, widget=forms.PasswordInput(render_value=True))
  verify_password = forms.CharField(label="Verify Password", required=True, widget=forms.PasswordInput(render_value=True))
  password_hint = forms.ChoiceField(label = "Password Hint",required = True,
      choices =( ("", "(select a security question)"),
                  ("A", "What is your Mother's Maiden Name?" ),
                  ("B", "What city were you born in?" ),
                  ("C", "What is your pet's name?"), 
                  ("D", "What is your Father's Middle Name?"),
                  ("E", "What is your favorite sports team?")
                  )
      )
  #password_hint = forms.CharField(label="Password Hint", required=False)
  password_answer = forms.CharField(label="Password Hint Answer", required=True)
  # security_questions = forms.CharField(label="Security Question", required=False, initial=False)

  def clean(self):

    cleaned_data = super().clean()

    password = cleaned_data.get("password", None)
    verify_password = cleaned_data.get("verify_password", None)

    if password is None or verify_password is None:
        pass
    elif len(password) < 6:
        self.add_error("password", "Your password must be at least 6 characters")
    elif password != verify_password:
        self.add_error("password", "Passwords do not match")


    email = cleaned_data.get("email", None)
    verify_email= cleaned_data.get("verify_email", None)

    if email is None or verify_email is None:
        pass
    elif email != verify_email:
        self.add_error("email", "Email fields do not match")


class PrototypeJoinStudentAccountForm(JoinCreateAccountForm):
  pass


class PrototypeJoinStudentInformationForm(AddFormControlClassMixin, forms.Form):
    """
    Form for the first step of the student join process... verifification, etc.
    """

    verify = forms.BooleanField(
      label="I confirm that I am a current student actively enrolled in a college or university degree program.",
      required=True
      )

    school = forms.ChoiceField(
        choices=[("OTHER","Other")], 
        label="School",
        required = True,
    )
    other_school = forms.CharField(
        label = "Other school if yours is not listed above",
        required=False
    )
    degree_type_choice = forms.ChoiceField(
        label="Degree Type",
        choices=(
            ("PLANNING", "Planning"),
            ("ARCHITECTURE","Architecture"),
            ("ENGINEERING","Engineering"),
            ("ENIVIRONMENTAL_SCIENCE","Environmental Science"),
            ("GEOGRAPHY","Geography"),
            ("INTERNATIONAL_STUDIES","International Studies"),
            ("LANDSCAPE_ARCHITECTURE","Landscape Architecture"),
            ("POLITICAL_SCIENCE","Political Science"),
            ("PUBLIC_ADMINISTRATION","Public Administration"),
            ("PUBLIC_HEALTH","Public Health"),
            ("SOCIAL_WORK","Social Work"),
            ("SOCIOLOGY","Sociology"),
            ("URBAN_STUDIES","Urban Studies"),
            ("OTHER", "Other")
        ) )

    degree_type_other = forms.CharField(
      label="Other Degree Type",
      required=False)

    degree_level_choice = forms.ChoiceField(
        label="Degree Level",
        required=True,
        choices=(
            ("B","Undergraduate"),
            ("M","Graduate"),
            ("P","Post-Graduate (PhD, J.D., etc.)"),
            ("OTHER","Other")
        ) )
    degree_level_other = forms.CharField(
      label="Other Degree Level",
      required=False)

    expected_graduation_date = forms.DateField(
      label="Expected Graduation Date",
      required=True,
      widget=YearMonthDaySelectorWidget(
        year_sort="asc",
        max_year=datetime.datetime.today().year+20,
        min_year=datetime.datetime.today().year,
        include_day=False,
        attrs={"style":"width:auto;display:inline-block"})
      )

    def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.add_form_control_class()


class PrototypeStudentsAddDivisionsAndSubscriptionsForm(forms.Form):

    is_renewing = False # default is false
    is_student = False

    product_type_division = "DIVISION"
    product_type_chapter = "CHAPTER"
    product_type_subscription = "PUBLICATION_SUBSCRIPTION"

    planners_advocacy = forms.BooleanField(
        label="I want to join APA's Planners' Advocacy Network.",
        required=False
      )

    # FIELDS ARE ADDED DYNAMICALLY

    def __init__(self, *args, **kwargs):

        # THESE ARE PASSED IN
        self.active_division_codes = kwargs.pop("active_division_codes", []) # passed or processed? list of purchase records?...
        self.active_chapter_codes = kwargs.pop("active_chapter_codes", []) # passed or processed? list of purchase records?...
        self.active_subscription_codes = kwargs.pop("active_subscription_codes", []) # passed or processed? list of purchase records?...
        self.cart_purchases_qset = kwargs.pop("cart_purchases_qset", [])
        # self.contact = kwargs.get("contact", [])
        # self.user = self.contact.user

        super().__init__(*args, **kwargs)

        self.init_divisions_chapters_and_subscriptions_fields()

        # FOR STUDENTS, e-JAPA is included, so it's not a choice
        # PLANNING MAGAZINE is always included

    def init_divisions_chapters_and_subscriptions_fields(self):

        # get choices from products
        self.available_products = ProductCart.objects.filter(
            product_type=self.product_type_division
        ).prefetch_related(# using prefetch_related to prepare for get_price()
            "options",
            "prices__required_groups", 
            "prices__required_product_options",
            "content",
        ).order_by(
            "content__title"
        ) 
        
        self.division_products = [p for p in self.available_products]

        self.fields["divisions"] = forms.MultipleChoiceField(
          choices=[(p.code, p.content.title) for p in self.division_products], 
          widget=forms.CheckboxSelectMultiple(),
          required=False)





