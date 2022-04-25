from enum import Enum

# This is here because of circular import errors
TARGETED_CREDITS_TOPICS = (
    ("SUSTAINABILITY_AND_RESILIENCE", "Sustainability & Resilience"),
    )

# these are the primary content types... each with their own separate app
# dealing with specific models that inherit from content
CONTENT_TYPES = (
    ('PAGE', 'Web page'),
    ('EVENT', 'Events & training'),
    ('RFP', 'RFP/RFQ'),
    ('KNOWLEDGEBASE', 'Planning knowledgebase entry'),
    ('KNOWLEDGEBASE_COLLECTION', 'Planning knowledgebase collection'),
    ('KNOWLEDGEBASE_STORY', 'Planning knowledgebase story'),
    ('KNOWLEDGEBASE_SUGGESTION', 'Planning knowledgebase resource suggestion'),
    ('AWARD', 'Award nomination'),
    ('RESEARCH_INQUIRY', 'Research inquiry'),
    ('IMAGE', 'Image library image'),
    ('MEDIA', 'Media asset'),
    ("PRODUCT", "Other product"),
    ("PUBLICATION", "Publication (article or resource)"),
    ("BLOG", "Blog post"),
    ("EXAM", "Exam application submission"),
    ("JOB", "Job ad")
)


class ContentType(Enum):
    PAGE = "PAGE"
    PAGE_LABEL = "Web page"

    EVENT = "EVENT"
    EVENT_LABEL = "Events & training"

    RFP = "RFP"
    RFP_LABEL = "RFP/RFQ"

    KNOWLEDGEBASE = "KNOWLEDGEBASE"
    KNOWLEDGEBASE_LABEL = "Planning knowledgebase entry"

    KNOWLEDGEBASE_COLLECTION = "KNOWLEDGEBASE_COLLECTION"
    KNOWLEDGEBASE_COLLECTION_LABEL = "Planning knowledgebase collection"

    KNOWLEDGEBASE_STORY = "KNOWLEDGEBASE_STORE"
    KNOWLEDGEBASE_STORY_LABEL = "Planning knowledgebase story"

    KNOWLEDGEBASE_SUGGESTION = "KNOWLEDGEBASE_SUGGESTION"
    KNOWLEDGEBASE_SUGGESTION_LABEL = "Planning knowledgebase resource suggestion"

    AWARD = "AWARD"
    AWARD_LABEL = "Award nomination"

    RESEARCH_INQUIRY = "RESEARCH_INQUIRY"
    RESEARCH_INQUIRY_LABEL = "Research inquiry"

    IMAGE = "IMAGE"
    IMAGE_LABEL = "Image library image"

    MEDIA = "MEDIA"
    MEDIA_LABEL = "Media asset"

    PRODUCT = "PRODUCT"
    PRODUCT_LABEL = "Other product"

    PUBLICATION = "PUBLICATION"
    PUBLICATION_LABEL = "Publication (article or resource)"

    BLOG = "BLOG"
    BLOG_LABEL = "Blog post"

    EXAM = "EXAM"
    EXAM_LABEL = "Exam application submission"

    JOB = "JOB"
    JOB_LABEL = "Job ad"

# primarly for pages, these categorize content into main areas based on the
# APA sitemap so that proxy models can be associated with each of these content areas
# for the sake of managing permissions, admin form tweaks, and custom logic
# TO DO... (consider making a model for this...)
CONTENT_AREAS = (
    ("NONE", "Uncategorized pages"),
    ("MEMBERSHIP", "Membership"),
    ("KNOWLEDGE_CENTER", "Knowledge Center"),
    ("CONFERENCES", "Conferences and Meetings"),
    # ("RESEARCH", "Research and PAS"), # research is broken out from knowledge center in order to help organize content management assignments/access
    ("AICP", "AICP"),
    ("POLICY", "Policy and Advocacy"),
    ("CAREER", "Career Center"),
    ("OUTREACH", "Community Outreach"),
    ("CONNECT", "Connect with APA"),
    ("ABOUT", "About"),
    # separate content areas???
    # ("CHAPTERS", "Chapters"),
    # ("DIVISIONS", "Divisions"),
)

# Used for educational content and publications, drills down resources into more specific types
RESOURCE_TYPES = (
    ('BOOK', 'Book'), # TO DO: consider removing BOOK/EBOOK
    ('EBOOK', 'E-Book'),
    ('ARTICLE', 'Article'),
    ('REPORT', 'Report'),
    ('PUBLICATION_DOCUMENT', 'Publication Document'),
    ('TOOLKIT', 'Toolkit'),
    ('E_LEARNING', 'E-Learning'), # for all e-learning... this should include on-demand courses and live online events
    # more to be added here...
)

# NOTE: this is the "visibility status" of the content
STATUSES = (
    ('A', 'Active'),
    ('P', 'Pending'),
    ('I', 'Inactive'),
    ('H', 'Hidden'),
    ('S', 'Staff-Use Only'),
    ('X', 'Marked for Deletion'),
    # TO DO... these statsus DON'T make sense for all content... remove from here?
    ('N', 'Not Complete'),  # TO DO... may want to remove, applies only to awards
    ('C', 'Complete'),  # TO DO... may want to remove, applies only to awards
    ('CA', 'Cancelled'), #if the cancelled status is changed.. Appropriate changes should be made in events/views/events_reports_views.py for cancelled reports
)


class ContentStatus(Enum):

    ACTIVE = "A"
    ACTIVE_LABEL = "Active"

    PENDING = "P"
    PENDING_LABEL = "Pending"

    INACTIVE = "I"
    INACTIVE_LABEL = "Inactive"

    HIDDEN = "H"
    HIDDEN_LABEL = "Hidden"

    STAFF_USE_ONLY = "S"
    STAFF_USE_ONLY_LABEL = "Staff-Use Only"

    MARKED_FOR_DELETION = "X"
    MARKED_FOR_DELETION_LABEL = "Marked for Deletion"

    NOT_COMPLETE = "N"
    NOT_COMPLETE_LAEBL = "Not Complete"

    COMPLETE = "C"
    COMPLETE_LABEL = "Complete"

    CANCELLED = "CA"
    CANCELLED_LABEL = "Cancelled"


WORKFLOW_STATUSES = (
    ('DRAFT_IN_PROGRESS', 'Draft in progress'),
    ('NEEDS_REVIEW', 'Needs review'),
    ('NEEDS_WORK', 'Needs work'),
    ('APPROVED_TO_PUBLISH', 'Approved to publish'),
    ('IS_PUBLISHED', 'Published'),
    ('UNPUBLISHED', 'Unpublished'),
)


class WorkflowStatus(Enum):
    DRAFT_IN_PROGRESS = "DRAFT_IN_PROGRESS"
    DRAFT_IN_PROGRESS_LABEL = "Draft in progress"

    NEEDS_REVIEW = "NEEDS_REVIEW"
    NEEDS_REVIEW_LABEL = "Needs review"

    NEEDS_WORK = "NEEDS_WORK"
    NEEDS_WORK_LABEL = "Needs work"

    APPROVED_TO_PUBLISH = "APPROVE_TO_PUBLISH"
    APPROVED_TO_PUBLISH_LABEL = "Approved to publish"

    IS_PUBLISHED = "IS_PUBLISHED"
    IS_PUBLISHED_LABEL = "Published"

    UNPUBLISHED = "UNPUBLISHED"
    UNPUBLISHED_LABEL = "Unpublished"


PUBLISH_STATUSES = (
    ('DRAFT', 'Draft'),
    ('PUBLISHED', 'Published'),
    ('SUBMISSION', 'Submission'),
    ('EARLY_RESUBMISSION', 'Early Resubmission'),
)


class PublishStatus(Enum):
    DRAFT = "DRAFT"
    DRAFT_LABEL = "Draft in progress"

    PUBLISHED = "PUBLISHED"
    PUBLISHED_LABEL = "Published"

    SUBMISSION = "SUBMISSION"
    SUBMISSION_LABEL = "Submission"

    EARLY_RESUBMISSION = "EARLY_RESUBMISSION"
    EARLY_RESUBMISSION_LABEL = "Early Resubmission"


LANGUAGES = (
    ("EN", "English"),
    ("FR", "French"),
    ("ZH", "Chinese"),
    ("ES", "Spanish")
)

QUESTION_TYPES = (
    ("LONG_TEXT","Long Text"),
    ("SHORT_TEXT","Short Text"),
    ("CHECKBOX","Checkbox"),
    ("CHECKBOX_FINAL", "Final Step Checkbox")
)

IMAGE_TYPES = (
    ("BANNER", "Banner Image"),
    # ("BANNER_CENTERED", "Banner Image - Centered),
    ("THUMBNAIL", "Thumbnail")
)

TEMPLATES = (
    ("pages/newtheme/default.html","Default web page"),
    ("cm/newtheme/aicp-page-sidebar.html", "AICP branded page with sidebar"),
    ("blog/newtheme/post.html","Blog Post"),
    ("store/newtheme/foundation/page-sidenav.html", "Foundation branded page with sidebar"),
    ("knowledgebase/newtheme/collection.html", "Knowledgebase collection template"),
    ("knowledgebase/newtheme/resource.html", "Knowledgebase resource template"),
    ("knowledgebase/newtheme/story.html", "Knowledgebase story template"),
    ("events/newtheme/eventmulti-details.html", "Multipart event template"),
    ("events/newtheme/ondemand/course-details.html", "On-demand template"),
    ("learn/newtheme/course-details.html", "APA Learn course template"),
    ("publications/newtheme/planning-mag.html","Planning Magazine article (OLD)"),
    ("publications/newtheme/planning-mag-article.html","Planning Magazine article"),
    ("store/newtheme/product/details.html", "Product template"),
    ("publications/newtheme/publication-document.html", "Publication document template"),
    ("pages/newtheme/research.html","Research project"),
    ("pages/newtheme/section-overview.html", "Section overview page"),
    ("events/newtheme/event-details.html", "Single event or activity template"),
    ("pages/newtheme/landing.html","Topic landing page"),
    ("pages/newtheme/full-width.html", "Full Width (no side nav)"),
    ("newtheme/templates/conference/page-ads.html", "Conference (Original Page Template)"),
    ("newtheme/templates/conference/page-widget.html", "Conference Page WITH Sidebar AND WIDGET"),
    ("newtheme/templates/conference/page-sidebar.html", "Conference Page WITH Sidebar (general)"),
    ("newtheme/templates/conference/page-nosidebar.html", "Conference Page WITHOUT Sidebar"),
    ("events/newtheme/conference-details.html", "Conference Activity Details"),
    ("events/newtheme/conference-details-embed.html", "Conference Activity Details WITH Embed"),
    ("conference/newtheme/home.html", "Conference Home"),
    ("pages/micro/home.html", "Micro home page"),
    ("pages/micro/default.html","Micro default page"),
    ("pages/micro/section-overview.html", "Micro section overview page"),
    ("pages/micro/landing.html","Micro topic landing page"),
    ("pages/micro/home/default.html","Home default page"),
    ("pages/micro/home/section-overview.html", "Home section overview page"),
    ("pages/micro/home/landing.html","Home topic landing page"),
    ("pages/newtheme/media.html","Media Page"),
    ("pages/newtheme/jotform.html", "JotForm Page"),
)

OG_TYPES = (
    ("article", "article"),
    ("book", "book"),
    ("books.author", "books.author"),
    ("books.book", "books.book"),
    ("books.genre", "books.genre"),
    ("business.business", "business.business"),
    ("fitness.course", "fitness.course"),
    ("game.achievement", "game.achievement"),
    ("music.album", "music.album"),
    ("music.playlist", "music.playlist"),
    ("music.radio_station", "music.radio_station"),
    ("music.song", "music.song"),
    ("place", "place"),
    ("product", "product"),
    ("product.group", "product.group"),
    ("product.item", "product.item"),
    ("profile", "profile"),
    ("restaurant.menu", "restaurant.menu"),
    ("restaurant.menu_item", "restaurant.menu_item"),
    ("restaurant.menu_section", "restaurant.menu_section"),
    ("restaurant.restaurant", "restaurant.restaurant"),
    ("video.episode", "video.episode"),
    ("video.movie", "video.movie"),
    ("video.other", "video.other"),
    ("video.tv_show", "video.tv_show")
)


# THE CODE is the Page.code of the micro conf home page -- the trick is that the code
# must be set on the back end

# THE CODE is the Page.code of the micro conf home page
# this is being used as a dictionary, not a choices tuple, not involved in migrations
CONF_LANDING_CODES = (
    ("conference", "CONFERENCE_HOME"),
    ("policy", "POLICY_HOME"),
    ("water", "WATER_HOME"),
    )

# this is being used as a dictionary, not a choices tuple, not involved in migrations
CONF_CACHE_FILES = (
    ("CONFERENCE_HOME", "conferencemenu-query.p"),
    ("POLICY_HOME", "policymenu-query.p"),
    ("WATER_HOME", "watermenu-query.p"),
    )


DEFAULT_SITEMAP_KWARGS = dict(
    publish_status=PublishStatus.PUBLISHED.value,
    status=ContentStatus.ACTIVE.value
)

MINIMUM_YEAR = 1900
