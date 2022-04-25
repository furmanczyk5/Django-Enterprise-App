# change directory to _deploy
cd $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
. local_settings.sh
. prod_settings.sh

deploy_server=$deploy_server_1

clear

color="\x1B[0;32m"
color_error="\x1B[0;31m"
color_prompt="\x1B[0;33m"
color_input="\x1B[0;43m"
no_color="\x1B[0m" 

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

show_msg 'SHELL ON PROD:'

cd "$deploy_repo_path"
check_error_exit

show_msg 'ACTIVATING planning VIRTUAL ENVIRONMENT...'
source "$deploy_venv_path"/bin/activate
check_error_exit
echo '...activated'

python manage.py shell
"