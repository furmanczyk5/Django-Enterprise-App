#!/usr/bin/env bash

clear

color="\x1B[0;32m"
color_error="\x1B[0;31m"
color_prompt="\x1B[0;33m"
color_input="\x1B[0;43m"
no_color="\x1B[0m"

echo -e ${no_color}

# ----------------------------------------------------------------------------
# FUNCTIONS:

prompt_value=""
function prompt
{
    prompt_value=""
    echo -e ${color_prompt}
    echo "$1"
    echo -e ${color_input}
    read -p "" prompt_value
    echo -e ${no_color}
}

function show_msg
{
    if [ $2 ]
    then
        msg_color=$2
    else
        msg_color=$color
    fi
    echo -e ${msg_color}
    echo "--------------------------------------------------------------------------"
    echo $1
    echo -e ${no_color}
}

function check_error_exit
{
    if [ $? != 0 ]
    then
        show_msg "ERROR: EXITING SCRIPT... " $color_error
        exit 1
    fi
}

function attempt_merge_branch
{
    # TO DO... better merge commit msg (showing whether auto tests ran, and any conflicts)
    git merge $1 -m "Merge '$1' into '$2'"
    if [ $? != 0 ]
    then
        show_msg "MERGE CONFLICT: fix conflicts in these files, then enter commit msg for merge..." $color_error

        git diff --name-only --diff-filter=U

        read -p "Merge commit msg:" merge_commit_msg

        git add --all .
        git commit -m "$merge_commit_msg"
        # is this recursion appropriate/necessary...?
        attempt_merge_branch $1 $2
    fi
}
# ----------------------------------------------------------------------------
# set variables for either staging or prod deployment:
if [ "$2" == "staging" ]
then
    . staging_settings.sh

elif [ "$2" == "prod" ]
then
    . prod_settings.sh

else
    show_msg "ERROR: MUST SPECIFY 'staging', or 'prod'" $color_error
    exit 1
fi

# ----------------------------------------------------------------------------
if [ $milestone_warn != 0 ]
then
    show_msg "WARNING!!!!!!!!!" $color_error
    show_msg "WARNING!!!!!!!!!" $color_error
    show_msg "WARNING!!!!!!!!!" $color_error
    show_msg "You are attempting to deploy a branch to prod that has all the milestone commits from the past 2 months.
    You should not continue unless you are intending to deploy the ENTIRE milestone with everyone's updates RIGHT NOW." $color_error
    prompt "ARE YOU SHURE YOU WANT TO DEPLOY THE ENTIRE MILESTONE TO PROD? If yes, type 'MILESTONE' in all caps:"
    milestone_continue=$prompt_value
    if [ $milestone_continue != "MILESTONE" ]
    then
        exit 1
    fi
fi
# ----------------------------------------------------------------------------


show_msg "Deploying to $2..."

if [ "$3" == "full" ]
then
    deploy_full=1
else
    deploy_full=0
fi

deploy_migrations=0
if [ "$4" == "migrate" ]
then
    deploy_migrations=1
else
    deploy_migrations=0
fi



# ----------------------------------------------------------------------------

# change directory to _deploy and get local settings:
cd $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
. local_settings.sh
# change directory to repo root
cd ..



#activate virtual environment
. $venv_path/bin/activate
check_error_exit

#determine the current branch
branch_name=$(git symbolic-ref -q HEAD)
branch_name=${branch_name##refs/heads/}
branch_name=${branch_name:-HEAD}
check_error_exit



# TO DO... would be nice to color this!
#read -p "Branch name (ENTER to use current '$branch_name' branch):" new_branch_name

prompt "Specify branch name (ENTER to use current '$branch_name' branch):"
new_branch_name=$prompt_value


if [ "$new_branch_name" != "" ]
then
    branch_name=${new_branch_name}
    git checkout $branch_name
    check_error_exit
fi


if [ "$branch_name" == "staging" ]
then
    show_msg "ERROR: DON'T DEPLOY STAGING ANYWHERE DIRECTLY!!!!!!!" $color_error
    exit 1
fi

# MAYBE IN THE FUTURE... use this to read in user story # and do something with that (e.g. axosoft api call)
# read -p "User story # (ENTER for none):" user_story

# commit any changes
if [[ -n $(git status --porcelain) ]]; then
    prompt "You have changes in '$branch_name'. Specify commit msg to commit and continue:"
    commit_msg=$prompt_value
    show_msg "Committing changes and syncing with remote repo..."
    git add --all .
    git commit -m "$commit_msg"
    git pull --rebase
    check_error_exit
    git push
fi

# prompt "Ready to run auto tests on '$branch_name' branch (ENTER to continue or 's' to skip):"
# k_runtests=$prompt_value

# if [ "$k_runtests" != "s" ]
# then
#     show_msg "Running auto tests..."
#     python manage.py test
#     check_error_exit
#     # TO DO... save log file???
#     show_msg "HURRAY! Tests succeeded..."
# fi

# if [ "$1" == "milestone" ]
# then
#     show_msg "Now switching current branch to 'milestone' branch and merging '$branch_name' into 'milestone'..."
#     git checkout milestone
#     check_error_exit
#     git pull origin milestone
#     check_error_exit

#     attempt_merge_branch $branch_name milestone
#     check_error_exit

#     git push origin milestone
#     check_error_exit

#     show_msg "Now switching current branch to '$merge_to_branch_name' and merging 'milestone' into '$merge_to_branch_name'..."

#     # check out and pull latest of the staging/master branch:
#     git checkout $merge_to_branch_name
#     check_error_exit
#     git pull origin $merge_to_branch_name
#     check_error_exit

#     attempt_merge_branch milestone $merge_to_branch_name
#     check_error_exit
# else
    show_msg "Now switching current branch to '$merge_to_branch_name' and merging '$branch_name' into '$merge_to_branch_name'..."

    # check out and pull latest of the staging/master branch:
    git checkout $merge_to_branch_name
    check_error_exit
    git pull origin $merge_to_branch_name
    check_error_exit

    attempt_merge_branch $branch_name $merge_to_branch_name
    check_error_exit
# fi



# install any new requirements (now that we're merged on deployemnt branch)... that way auto testing won't break
show_msg "HURRAY! Merge(s) succeeded... "

if [ "$deploy_full" == 1 ]
then
    show_msg "installing new/updated python modules locally now that we're merged into '$merge_to_branch_name' branch..."
    pip install -r requirements.txt
    check_error_exit
fi

prompt "Ready to run auto tests on '$merge_to_branch_name' branch (ENTER to continue or 's' to skip):"
k_runtests=$prompt_value

if [ "$k_runtests" != "s" ]
then
    show_msg "Running auto tests..."
    python manage.py test
    # TO DO... save log file???
    if [ $? != 0 ]
    then
        show_msg "OH NO: Auto tests failed! Resetting local '$merge_to_branch_name' to remote 'origin/$merge_to_branch_name' to undo merge..." $color_error
        git fetch origin
        git reset --hard origin/$merge_to_branch_name
        # check out the original branch again
        git checkout $branch_name
        exit 1
    fi
    show_msg "HURRAY! Tests succeeded..."
fi

show_msg "Now pushing '$merge_to_branch_name' to remote repo..."

# push merged deployment branch to remote
git push origin $merge_to_branch_name
check_error_exit
# check out the original branch again
git checkout $branch_name

if [[ $2 == "prod" ]]
then
    deploy_server=$deploy_server_1
    show_msg "SSH-ing to run deployment script on remote server: $deploy_server"
    . _deploy/deploy_to_server.sh
    deploy_server=$deploy_server_2
    show_msg "SSH-ing to run deployment script on remote server: $deploy_server"
    . _deploy/deploy_to_server.sh
    # # COMMENTING OUT DEPLOY TO SEPARATE CELERY SERVER UNTIL WE NEED IT
    # deploy_server=$deploy_server_3
    # show_msg "SSH-ing to run deployment script on remote server: $deploy_server"
    # . _deploy/deploy_to_server.sh
else
    show_msg "SSH-ing to run deployment script on remote server: $deploy_server"
    . _deploy/deploy_to_server.sh
fi

show_msg "SUCCESS!!! Deployment complete."

# MAYBE IN THE FUTURE: use axosoft API to mark user story as staging-review / prod-review
# MAYBE IN FUTURE: (when we have updated mantis) ... use mantis API to mark ticket as testing/rolled-to-prod

