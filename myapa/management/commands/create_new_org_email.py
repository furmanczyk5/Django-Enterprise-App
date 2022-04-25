from django.core.management.base import BaseCommand

from content.models.email_template import EmailTemplate


class Command(BaseCommand):
    help = """Updates or creates the MYORG_NEW_ORG_RECORD EmailTemplate"""

    email_data = dict(
        code="MYORG_NEW_ORG_RECORD",
        title="MYORG_NEW_ORG_RECORD",
        email_from="customerservice@planning.org",
        subject="A new Organization record has just been created on planning.org",
        body="""<p>{{ contact }} just created an Organization record for {{ org }}</p>
        {% if ein_candidates %}
        <p><strong>This new record's EIN ({{ org.ein_number }}) matches the following existing Organization records with the same EIN:</strong></p>
        <ul>
            {% for ein_candidate in ein_candidates %}
            <li><strong>{{ ein_candidate.user.username }} | {{ ein_candidate.company }}</strong></li>
            <li>EIN: {{ ein_candidate.ein_number }}</li>
            {% endfor %}
        </ul>
        {% endif %}
        
        {% if dupe_candidates %}
        <p><strong>This new record may be a duplicate of the following existing records:</strong></p>
        <ul>
            {% for dupe_candidate in dupe_candidates %}
            <li><strong>{{ dupe_candidate.id }} | {{ dupe_candidate.company }}</strong></li>
            <ul>
                {% if dupe_candidate.website %} <li>{{ dupe_candidate.website }}</li> {% endif %}
                <li>{{ dupe_candidate.full_address }}</li>
            </ul>
            {% endfor %}
        </ul>
        {% endif %}
        """
    )

    def handle(self, *args, **options):
        et, _ = EmailTemplate.objects.get_or_create(code=self.email_data['code'])
        et.__dict__.update(self.email_data)
        et.save()
        self.stdout.write(
            self.style.SUCCESS(
                "Created or updated {} email template".format(self.email_data['code'])
            )
        )
