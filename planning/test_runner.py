from django.db import connections
from django.test.runner import DiscoverRunner
from django.test import utils


class UseLiveDatabaseTestRunner(DiscoverRunner):
    """
    https://docs.djangoproject.com/en/1.11/topics/testing/advanced/#using-different-testing-frameworks

    Test Runner that allows setting to test with live database

    Based on this github project
    https://github.com/boldprogressives/django-testrunner-use_live_db

    Here are a couple things to note.
        - It is not a good practice to run tests with live data, Django makes this difficult to do on purpose
        - DO NOT RUN TESTS WITH THIS ON PRODUCTION. We shouldn't be editing live databases
        - Only run this on dev or staging databases

    To test with a live database, set...
        DATABASE["USE_LIVE_FOR_TESTS"] = True
        DATABASE["TEST"]["NAME"] = DATABASE["NAME"]

    """

    def setup_databases(self, **kwargs):

        verbosity = self.verbosity
        interactive = self.interactive
        keepdb = self.keepdb
        debug_sql = self.debug_sql
        parallel = self.parallel

        test_databases, mirrored_aliases = utils.get_unique_databases_and_mirrors()

        old_names = []

        for signature, (db_name, aliases) in test_databases.items():
            first_alias = None

            #############################
            # THIS IS WHAT IS DIFFERENT
            connection = connections[next(iter(aliases))]
            if connection.settings_dict.get("USE_LIVE_FOR_TESTS"):
                # Then don't create this database
                continue
            #############################

            for alias in aliases:
                connection = connections[alias]
                old_names.append((connection, db_name, first_alias is None))

                # Actually create the database for the first connection
                if first_alias is None:
                    first_alias = alias
                    connection.creation.create_test_db(
                        verbosity=verbosity,
                        autoclobber=not interactive,
                        keepdb=keepdb,
                        serialize=connection.settings_dict.get("TEST", {}).get("SERIALIZE", True),
                    )
                    if parallel > 1:
                        for index in range(parallel):
                            connection.creation.clone_test_db(
                                number=index + 1,
                                verbosity=verbosity,
                                keepdb=keepdb,
                            )
                # Configure all other connections as mirrors of the first one
                else:
                    connections[alias].creation.set_as_test_mirror(
                        connections[first_alias].settings_dict)

        # Configure the test mirrors.
        for alias, mirror_alias in mirrored_aliases.items():
            connections[alias].creation.set_as_test_mirror(
                connections[mirror_alias].settings_dict)

        if debug_sql:
            for alias in connections:
                connections[alias].force_debug_cursor = True

        return old_names

