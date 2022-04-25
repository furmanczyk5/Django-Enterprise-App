from .claims import CMSearchView, CMLiveEventSearchView, CMOnDemandSearchView, LogView, \
    ClaimDeleteView, ClaimFormBaseView, EventClaimFormView, EventClaimConfirmationView, \
    AuthorClaimFormView, SelfReportClaimFormView, ClaimDetailsView

from .providers import (ProviderApplicationView, ProviderPastApplicationView,  ProviderEventComments,
    ProviderSearchView, ProviderDetails, ProviderCommentsView,
    ProviderRegistrationView, ProviderRegistration2015View, ProviderNewRecord, SpeakerConfirmRole,
    ProviderApplicationSubmissionReviewView, ProviderApplicationSubmissionConfirmationView, redirect_to_myorg)
