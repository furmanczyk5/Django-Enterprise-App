deploy_server_1="138.197.62.157"
deploy_server_2="165.227.248.67"

deploy_venv_path="/srv/sites/apa/envs/apa"
deploy_repo_path="/srv/sites/apa/proj/apa"

merge_to_branch_name="master"

color="\x1B[0;32m"
color_error="\x1B[0;31m"
color_prompt="\x1B[0;33m"
color_input="\x1B[0;43m"
no_color="\x1B[0m"

# set this to 1 on the "milestone" code branch to make sure that this is NOT
# accidentally pushed to prod unless it's supposed to be
milestone_warn=0
