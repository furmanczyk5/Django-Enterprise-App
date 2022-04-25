#!/usr/bin/env bash

if [ -z $VIRTUAL_ENV ]
then
    echo "ERROR: virtualenv not activated"
    exit 1
fi

python -Wmodule manage.py test --verbosity=2 --keepdb content.tests.test_publish events jobs knowledgebase publications
