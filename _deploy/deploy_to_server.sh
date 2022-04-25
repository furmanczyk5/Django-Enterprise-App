#!/usr/bin/env bash

ssh -t $deploy_user@$deploy_server "

function show_msg
{
    echo
    echo -e '"${color}"'
    echo '--------------------------------------------------------------------------'
    echo \$1
    echo -e '"${no_color}"'
}

function check_error_exit
{
    if [ \$? != 0 ]
    then
        echo -e '"${color_error}"'
        echo '--------------------------------------------------------------------------'
        echo 'ERROR: EXITING SCRIPT' 1>&2
        echo -e '"${no_color}"'
        exit 1
    fi
}

cd "$deploy_repo_path"
check_error_exit

show_msg 'ACTIVATING VIRTUAL ENVIRONMENT...'
source "$deploy_venv_path"/bin/activate
check_error_exit
echo '...activated'

export DJANGO_SETTINGS_MODULE=planning.settings.local

show_msg 'FETCHING "$merge_to_branch_name" CODE FROM REMOTE REPO...'
# (just to make sure on the right branch)
git checkout "$merge_to_branch_name"
check_error_exit
git fetch origin "$merge_to_branch_name"
check_error_exit
git reset --hard origin/"$merge_to_branch_name"

if [ "$deploy_full" == 1 ]
then
    show_msg 'INSTALLING PYTHON MODULES...'
    # (in theory... pip should not need sudo... but have had trouble without it in the past... modify?):
    pip install -r requirements.txt
    check_error_exit
fi

if [ "$deploy_migrations" == 1 ]
then
    show_msg 'MIGRATING DB:'
    python manage.py migrate
    check_error_exit
fi

if [ "$deploy_full" == 1 ]
then
    show_msg 'COLLECTING STATIC FILES...'
    python manage.py collectstatic --noinput
    check_error_exit
fi

show_msg 'RESTARTING django planning SERVICE...'
sudo supervisorctl restart django
check_error_exit

show_msg 'NOT restarting nodejs-server SERVICE...Please check for unexpected or silent errors, especially with syncing to/from iMIS.'
#show_msg 'Temporarily re-enabling node for posting CM log'
#sudo supervisorctl restart node
#check_error_exit

if [ "$deploy_full" == 1 ]
then
    show_msg 'RESTARTING celery SERVICE...'
    sudo supervisorctl restart celery
    check_error_exit
fi

if [ "$deploy_full" == 1 ] && [ -f '/etc/init.d/celerybeat' ]
then
    show_msg 'RESTARTING celerybeat SERVICE...'
    sudo supervisorctl restart celerybeat
    check_error_exit
fi
"
