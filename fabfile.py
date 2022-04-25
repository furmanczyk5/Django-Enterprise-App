import os
from fabric.api import *
from fabric.colors import *
from fabric.contrib.files import *
from contextlib import contextmanager
################################################
"""
This needs to run with Python 2.7 (so run it outside of the virtualenv)
Syntax: fab <environment_name> <action>
Example: fab production deploy_full

Install:
- Create a python module in this directory called fab_environments.py.
- Copy the imports above into that file module.
- Copy the production() function below and rename it to
something else, like development() or local_development()
This will be the environment_name passed in as the first
argument to the script.
- Customize the function and update the settings for the
corresponding server.

Note: the fab_environments.py will not be part of version control.

Here is an example of a Fabric Environment Settings Function (FESF)
to put in your fab_environments.py file.


import os
from fabric.api import *
from fabric.colors import *
from fabric.contrib.files import *

def staging():
    env.hosts = [ "rwest@159.203.94.74:22"]  # the host and ssh port
    env.project_name = "planning"       # keep this as-is
    env.client_name = "planning"       # keep this as-is
    env.django_supervisor_process = "django"
    env.nginx_supervisor_process = "nginx"
    # keep this as-is unless you relocate the project
    env.environment_dir = os.path.join("/", "iscape", "sites", env.project_name)
    # keep this as-is unless you relocate the virtualenv
    env.virtualenv_dir = os.path.join(env.environment_dir, 'envs', env.project_name)
    env.project_dir = os.path.abspath(os.path.join('.'))
    env.requirements_txt = os.path.abspath(os.path.join(env.project_dir, 'requirements.txt'))
    env.manage_py = os.path.abspath(os.path.join(env.project_dir, 'manage.py'))
    env.git_branch = "staging"  # Git branch to deploy from
    env.git_remote = "origin"

def prod():
    env.hosts = [ "rwest@104.131.105.101:22", "rwest@159.203.98.241:22"]  # the host and ssh port
    env.project_name = "planning"       # keep this as-is
    env.client_name = "planning"       # keep this as-is
    env.django_supervisor_process = "django"
    env.nginx_supervisor_process = "nginx"
    # keep this as-is unless you relocate the project
    env.environment_dir = os.path.join("/", "iscape", "sites", env.project_name)
    # keep this as-is unless you relocate the virtualenv
    env.virtualenv_dir = os.path.join(env.environment_dir, 'envs', env.project_name)
    env.project_dir = os.path.abspath(os.path.join('.'))
    env.requirements_txt = os.path.abspath(os.path.join(env.project_dir, 'requirements.txt'))
    env.manage_py = os.path.abspath(os.path.join(env.project_dir, 'manage.py'))
    env.git_branch = "master"  # Git branch to deploy from
    env.git_remote = "origin"

"""


################################################

try:
    from fab_environments import *
except:
    pass


##################################################################
# Define utility code here

@contextmanager
def activate():
    print(green("Activating: %s" % (env.virtualenv_dir)))
    with prefix("source %s" % os.path.join(env.virtualenv_dir, 'bin', 'activate')):
        yield


class VenvCommandSet(object):
    @classmethod
    def run_cmds(cls, commands):
        with activate():
            print(green("Showing: cd %s" % (env.project_dir)))
            with cd(env.project_dir):
                for command in commands:
                    command.run_cmd()

##################################################################
# Define Management Commands here


class HelpCommand(object):
    @classmethod
    def run_cmd(cls):
        cmd = 'python %s help' % (env.manage_py)
        print(green("Showing: %s" % (cmd)))
        run(cmd)


class GitPullCommand(object):
    @classmethod
    def run_cmd(cls):
        cmd = 'git pull %s %s' % (env.git_remote, env.git_branch)
        print(green("Showing: %s" % (cmd)))
        run(cmd)


class GitCheckoutBranchCommand(object):
    @classmethod
    def run_cmd(cls):
        cmd = 'git checkout -B %s %s/%s' % (env.git_branch, env.git_remote, env.git_branch)
        print(green("Showing: %s" % (cmd)))
        run(cmd)


class GitMergeCommand(object):
    @classmethod
    def run_cmd(cls):
        cmd = 'git merge %s/%s' % (env.git_remote, env.git_branch)
        print(green("Showing: %s" % (cmd)))
        run(cmd)


class GitFetchCommand(object):
    @classmethod
    def run_cmd(cls):
        cmd = "git fetch %s" % (env.git_remote)
        print(green("Showing: %s" % cmd))
        run(cmd)


class PipIntallCommand(object):
    @classmethod
    def run_cmd(cls):
        with cd(env.project_dir):
            cmd = """pip install -r %s""" % (env.requirements_txt)
            print(green("Showing: %s" % cmd))
            run(cmd)


class MigrateCommand(object):
    @classmethod
    def run_cmd(cls):
        cmd = 'python %s migrate --noinput' % (env.manage_py)
        print(green("Showing: %s" % cmd))
        run(cmd)


class CollectstaticCommand(object):
    @classmethod
    def run_cmd(cls):
        cmd = 'python %s collectstatic --noinput' % (env.manage_py)
        print(green("Showing: %s" % cmd))
        run(cmd)


class CompressCommand(object):
    @classmethod
    def run_cmd(cls):
        cmd = 'python %s compress' % (env.manage_py)
        print(green("Showing: %s" % cmd))
        run(cmd)


class RestartDjangoCommand(object):
    @classmethod
    def run_cmd(cls):
        cmd = 'supervisorctl restart %s' % (env.django_supervisor_process)
        print(green("Showing: %s" % cmd))
        sudo(cmd)


class RestartNginxCommand(object):
    @classmethod
    def run_cmd(cls):
        cmd = 'supervisorctl restart %s' % (env.nginx_supervisor_process)
        print(green("Showing: %s" % cmd))
        sudo(cmd)

#
##################################################################
# Fabric Command line actions


def help():
    VenvCommandSet.run_cmds([HelpCommand])


def collectstatic():
    VenvCommandSet.run_cmds([CollectstaticCommand])


def install_requirements():
    VenvCommandSet.run_cmds([PipIntallCommand])


def git_pull():
    VenvCommandSet.run_cmds([GitPullCommand])


def git_checkout_branch():
    VenvCommandSet.run_cmds([GitFetchCommand, GitCheckoutBranchCommand])


def migrate():
    VenvCommandSet.run_cmds([MigrateCommand])


def restart_django():
    VenvCommandSet.run_cmds([RestartDjangoCommand])


def restart_nginx():
    VenvCommandSet.run_cmds([RestartNginxCommand])


def deploy_full():
    """
    Deploy code with git, install requirements, syncdb, migrate, collectstatic, restart
    """
    VenvCommandSet.run_cmds([
        GitPullCommand, PipIntallCommand,
        MigrateCommand, CollectstaticCommand, RestartDjangoCommand, ])


def deploy_light():
    """
    Deploy code with git, collectstatic, restart
    """
    VenvCommandSet.run_cmds([GitPullCommand, CollectstaticCommand, RestartDjangoCommand, ])
