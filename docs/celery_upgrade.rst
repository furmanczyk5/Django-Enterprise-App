##############
Celery Upgrade
##############

Instructions on how to upgrade Celery in your local environment. Your working tree should be clean (e.g. ``git status`` shows no changed or untracked files). Then

.. code-block:: sh

    git checkout master
    git fetch origin --prune

First, stop any running Celery workers or beat instances. Until now we had been starting Celery with

.. code-block:: sh

    python manage.py celeryd --loglevel INFO

This would have been done in a separate terminal from ``python manage.py runserver``, so unless you had been working on something Celery-related very recently you likely don't have any workers or beat schedulers running.

It's probably a good idea to stop ``rabbitmq`` (our message broker for Celery).

.. code-block:: sh

    brew services stop rabbitmq

Speaking of RabbitMQ, now is probably a good time to ensure that is up-to-date as well.

.. code-block:: sh

    brew update
    brew upgrade

If brew did upgrade it, it likely auto-started it again, so be sure it's stopped with ``brew services stop rabbitmq``.

We previously used a package called ``django-celery`` to integrate Celery and Django, but recent versions of Celery integrate directly with Django and do not require this other third-party library. Uninstall it:

.. code-block:: sh

    pip uninstall django-celery

We also used this now-deprecated serialization library that's also not needed with the default ``pickle`` serializer. Uninstall this as well:

.. code-block:: sh

    pip uninstall django-cereal

Finally, there was this phantom ``src`` directory that seemed to be used for a Python/Celery-related library that was fetched directly from GitHub instead of PyPi - it's not needed anymore, so let's tidy up:

.. code-block:: sh

    # (in the project root)
    rm -r src

Now you should be able to pull down the changes from ``master``:

.. code-block:: sh

    git pull origin master

Start RabbitMQ:

.. code-block:: sh

    brew services start rabbitmq

Install/upgrade new requirements:

.. code-block:: sh

    pip install -r requirements.txt

Run migrations (for the Celery result backend from third-party libraries; none of our models are directly affected):

.. code-block:: sh

    python manage.py migrate

Now you can start a worker and the beat scheduler simultaneously with:

.. code-block:: sh

    celery worker -A planning.celery -B -l info

If it seems to be working (try changing your address in MyAPA and watch the terminal output to see if it runs the ``vv_validate_address_imis`` task), you should merge ``master`` in to your in-progress branches.
