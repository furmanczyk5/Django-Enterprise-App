from enum import Enum


class ProviderRestrictionMessages(Enum):

    DEFAULT = """<h1>Unauthorized</h1>
        <p>You do not have authorization to access this page.
        If you believe this is an error, please <a href="/customerservice/contact-us/">contact us</a>
        </p>"""

    NO_PROVIDER_ACCOUNT = """
            <h1>Create a New Provider Account</h1>
            <p>Our records indicate that your login is not yet associated with a CM Provider account.</p>
            <p><a class="button" href="/cm/provider/newrecord/">Create a New CM Provider Account</a></p>
            <p><em>If you believe you have reached this message in error, please contact us by using our <a href="https://www.planning.org/customerservice/contact-us/">customer service form</a>.</em></p>
            """
