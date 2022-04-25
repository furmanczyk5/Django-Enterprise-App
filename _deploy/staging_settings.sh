#!/usr/bin/env bash

deploy_server="165.227.181.116"

deploy_venv_path="/srv/sites/apa/envs/apa"
deploy_repo_path="/srv/sites/apa/proj/apa"

merge_to_branch_name="staging"

color="\x1b[1;36m"
color_error="\x1B[0;31m"
color_prompt="\x1B[0;33m"
color_input="\x1B[0;43m"
no_color="\x1B[0m"

milestone_warn=0 # not used on staging
