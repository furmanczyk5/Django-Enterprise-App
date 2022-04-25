# change directory to _deploy
cd $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
. local_settings.sh
. staging_settings.sh

clear

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

show_msg 'SHELL ON STAGING:'

cd "$deploy_repo_path"
check_error_exit

show_msg 'ACTIVATING planning VIRTUAL ENVIRONMENT...'
source "$deploy_venv_path"/bin/activate
check_error_exit
echo '...activated'

python manage.py shell
"