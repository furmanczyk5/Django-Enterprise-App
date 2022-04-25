from django.db import models

from content.models import BaseContent
from myapa.models.contact import Contact

TICKET_CATEGORIES = (
    ("ASC", "AICP Advanced Specialty Certification (ASC)"),
    ("AICP", "AICP Certification Exam"),
    ("LIBRARY", "APA Library"),
    ("FOUNDATION", "APA Foundation and Scholarships"),
    ("CAREER", "Career Services"),
    ("CM", "AICP Certification Maintenance"),
    ("CM_SPEAKERS", "AICP CM Speakers"),
    ("ETHICS", "Ethics"),
    ("FAICP", "AICP Fellows (FAICP)"),
    ("GREAT_PLACES", "Great Places in America"),
    ("JOBS", "Jobs Online/ RFPs and RFQs"),
    ("MEMBERSHIP", "Membership"),
    ("AWARDS", "National Planning Awards"),
    ("NPC", "National Planning Conference"),
    ("PAS", "PAS / Inquiry Answering Service"),
    ("EARLY_CAREER", "Student Membership"),
    ("CONTACT", "Update MyAPA Info. (email, phone, address)"),
    ("OTHER", "Other"),
    ("CONSULTANTS_ADVERTISING", "Consultants/Advertising"),
    ("AICP_CANDIDATE_PROGRAM", "AICP Candidate Program"),
    ("APA_LEARN", "APA Learn")
)

TICKET_STATUSES = (
    ("S", "Submitted"),
    ("P", "Pending"),
    ("IT", "Tech Issue - Handed Over to IT Support"),
    ("C", "Complete"),
    ("SP", "Spam")
)

CATEGORY_EMAIL_DICT = {
    "AICP": "aicpexam@planning.org",
    "BOOKSTORE": "customerservice@planning.org", # TO CO: consider removing...
    "LIBRARY": "library@planning.org",
    "CONTACT": "customerservice@planning.org",
    "WEBSITE": "website@planning.org",
    "CM": "AICPCM@planning.org",
    "CM_SPEAKERS": "CMSpeakerHelp@planning.org",
    "ASC": "asc@planning.org",
    "CPAT": "cpat@planning.org",
    "EARLY_CAREER": "studentmembership@planning.org",
    "ETHICS": "ethics@planning.org",
    "FAICP": "fellows@planning.org",
    "VOLUNTEER": "getinvolved@planning.org",
    "GREAT_PLACES": "greatplaces@planning.org",
    "JOBS": "customerservice@planning.org",
    "JOIN": "customerservice@planning.org",
    "MEMBERSHIP": "customerservice@planning.org",
    "AWARDS": "awards@planning.org",
    "NPC": "confregistration@planning.org",
    "PAS": "pas@planning.org",
    "FOUNDATION": "foundation@planning.org",
    "CAREER": "careerservices@planning.org",
    "OTHER": "customerservice@planning.org",
    "CONSULTANTS_ADVERTISING": "consultants@planning.org",
    "AICP_CANDIDATE_PROGRAM": "aicp@planning.org",
    "APA_LEARN": "customerservice@planning.org"
}


class Ticket(BaseContent):
    apa_id = models.CharField("APA ID #", max_length=10, blank=True, null=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    contact = models.ForeignKey(Contact, related_name="tickets", null=True, blank=True, on_delete=models.SET_NULL)
    category = models.CharField(max_length=50,
                                choices=sorted(TICKET_CATEGORIES, key=lambda x: x[1]))
    ticket_status = models.CharField(max_length=5, choices=TICKET_STATUSES, default='S')
    staff_comments = models.TextField(blank=True, null=True)

    @classmethod
    def category_to_support_email(cls, category):
        """
        NOTE:
        """
        return CATEGORY_EMAIL_DICT.get(category, "customerservice@planning.org")

    def get_support_email(self):
        return type(self).category_to_support_email(self.category)

    def save(self, *args, **kwargs):

        try:
            if self.apa_id and not self.contact:
                self.contact = Contact.objects.get(user__username=self.apa_id)
            elif self.contact and not self.apa_id:
                self.apa_id = self.contact.user.username
        except:
            pass

        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "support ticket"
