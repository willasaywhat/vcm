#!/usr/bin/env python
from urllib.parse import urlparse
import click
import os
import time
import configparser
from subprocess import call
import re

GLOBAL_CONFIG_LOCATION = '~/.vcm'
DEFAULT_NMAP_SETTINGS = ["-sV", "-p-"]

global_config = None


# TODO: Stuff to automate later
#   brew install testssl
#   download openssl binary and store it in default location
#   brew install nmap
#   brew install nikto


class VcmGlobalConfig:
    open_ssl_binary = '/usr/bin/openssl'  # default - can be overridden in global config file.

    def __init__(self):
        pass

    def read_global_vcm(self):
        global global_config

        print(f"Reading global config from {GLOBAL_CONFIG_LOCATION}")

        read_config = configparser.RawConfigParser()
        global_config_filename = os.path.expanduser(GLOBAL_CONFIG_LOCATION)
        read_config.read(global_config_filename)

        self.open_ssl_binary = read_config.get('GlobalSettings', 'openssl_binary')

    def write_global_vcm(self):
        print(f"Creating global config file with defaults in {GLOBAL_CONFIG_LOCATION}")

        global global_config
        global_config = configparser.RawConfigParser()
        global_config.add_section('GlobalSettings')

        global_config.set('GlobalSettings', 'openssl_binary', self.open_ssl_binary)

        global_config_file = os.path.expanduser(GLOBAL_CONFIG_LOCATION)

        with open(global_config_file, 'w') as configfile:
            try:
                global_config.write(configfile)
            except configparser.Error as ex:
                print(f"Error writing config file: {global_config_file} : {ex.message}")
                return


class VcmProjectConfig:
    local_folder = ''
    remote_folder = ''
    project_name = ''
    targets = []
    target_urls = []

    # derived directories
    artifacts_folder = ''

    def __init__(self):
        pass

    def read_project_vcm(self):
        project_config = configparser.RawConfigParser()

        project_filename = os.path.join(os.getcwd(), '.vcm')

        cf = project_config.read(project_filename)

        if len(cf) == 0:
            raise Exception(f"Unable to read config file: {project_filename}")

        self.remote_folder = project_config.get('ProjectSettings', 'remote_path')
        self.local_folder = project_config.get('ProjectSettings', 'local_path')

        self.artifacts_folder = os.path.join(self.local_folder, 'artifacts')

        url_targets = re.split(",", project_config.get('ProjectSettings', 'url_targets'))

        for t in url_targets:

            stripped_target = t.strip()

            # The requirement is for targets to have a scheme - even if you're just
            # using nmap
            if len(stripped_target) > 0:
                target_url = urlparse(stripped_target)

                self.target_urls.append(target_url)

                if not bool(target_url.scheme):
                    raise ValueError(
                        f"URL found without scheme: {stripped_target}. Please note, schemes are required for all URLs")

                self.targets.append(t)

    def write_project_vcm(self, project_name, local_folder, remote_folder, url_targets):
        project_config = configparser.RawConfigParser()
        project_config.add_section('ProjectSettings')
        project_config.set('ProjectSettings', 'project_name', project_name)
        project_config.set('ProjectSettings', 'local_path', os.path.join(local_folder, ''))
        project_config.set('ProjectSettings', 'remote_path', os.path.join(remote_folder, ''))
        project_config.set('ProjectSettings', 'url_targets', url_targets)

        project_vmc_filename = os.path.join(local_folder, '.vcm')

        with open(project_vmc_filename, 'w') as configfile:
            try:
                project_config.write(configfile)
            except configparser.Error as ex:
                print(f"Error writing config file: {project_vmc_filename} : {ex.message}")
                return


@click.group()
def vcm():
    global global_config
    global_config = VcmGlobalConfig()

    if os.path.isfile(os.path.expanduser(GLOBAL_CONFIG_LOCATION)):
        global_config.read_global_vcm()
    else:
        global_config.write_global_vcm()
    pass


###
#   Folder and project management
###
def create_folder(folder):
    if not os.path.exists(folder):
        try:
            os.makedirs(folder)
        except OSError as ex:
            print(f"Error creating folder: {folder} : {ex.strerror}")
            return


@vcm.command()
def create():
    # create a config file .vcm and ask for: project name, root dir name, remote directory, urls (csv)
    project_name = click.prompt('Project Name', type=str)
    local_folder = click.prompt('Local Path', type=str, default=os.path.join(os.getcwd(), project_name))
    remote_folder = click.prompt('Remote Path', type=str)
    url_targets = click.prompt('URL Targets (CSV)', type=str)

    create_folder(local_folder)

    for folder in ['reports', 'artifacts', 'logistics']:
        create_folder(os.path.join(local_folder, folder))

    project_config = VcmProjectConfig()
    project_config.write_project_vcm(project_name, local_folder, remote_folder, url_targets)


@vcm.command()
def push():
    # ensure the remote dir is mounted
    project_config = VcmProjectConfig()
    project_config.read_project_vcm()

    # do an rsync -ah from local to remote
    if click.confirm('Sync local (%s) to remote (%s)?' % (project_config.local_folder, project_config.remote_folder)):
        args = ["rsync", "-ah", "--progress", project_config.local_folder, project_config.remote_folder]
        call(args)


@vcm.command()
def pull():
    # ensure the remote dir is mounted
    # do an rsync -ah from remote to local
    project_config = VcmProjectConfig()
    project_config.read_project_vcm()

    # do an rsync -ah from local to remote
    if click.confirm('Sync remote (%s) to local (%s)?' % (project_config.remote_folder, project_config.local_folder)):
        args = ["rsync", "-ah", "--progress", project_config.remote_folder, project_config.local_folder]
        call(args)


###
#   Running testing tools
###
@vcm.group()
def run():
    pass


@run.command()
def nmap():
    try:
        project_config = VcmProjectConfig()
        project_config.read_project_vcm()
    except ValueError as ex:
        print(ex)
        return

    # We only need the netloc of the full url - strip the rest out
    nmap_targets = []
    for t in project_config.targets:
        nmap_targets.append(urlparse(t).netloc)

    if not click.confirm('Run nmap against the following targets: %s' % ', '.join(nmap_targets)):
        return

    args = ["nmap"]
    args.extend(DEFAULT_NMAP_SETTINGS)

    for t in nmap_targets:
        args.append(t)

    args.append("-oA")
    args.append(os.path.join(project_config.artifacts_folder, f'nmap_{time.time()}'))
    call(args)


@run.command()
def nikto():
    try:
        project_config = VcmProjectConfig()
        project_config.read_project_vcm()
    except ValueError as ex:
        print(ex)
        return

    if not click.confirm('Run nikto against the following targets: %s' % ', '.join(project_config.targets)):
        return

    # Nikto takes multiple hosts from a file
    # BUT bear in mind advice from: https://github.com/sullo/nikto/wiki/Basic-Testing
    # ie run scans separately so that memory is freed each time.
    for t in project_config.targets:
        output_filename = os.path.join(project_config.artifacts_folder,
                                       f"nikto_{urlparse(t).netloc}_{time.time()}.html")
        try:
            # nikto -h https://www.test.com -ssl -Format html -output .
            args = ["nikto", "-h", t, '-ssl', '-Format', 'html', '-output', output_filename]

            print(args)
            call(args)
        except Exception as ex:
            print(f"Error writing nikto output to: {output_filename} : {ex}")


@run.command()
def testssl():
    try:
        project_config = VcmProjectConfig()
        project_config.read_project_vcm()
    except ValueError as ex:
        print(ex)
        return

    https_targets = []
    for t in project_config.targets:
        https_targets.append('https://' + urlparse(t).netloc)

    if not click.confirm('Run testssl against the following targets: %s' % ', '.join(https_targets)):
        return

    for t in https_targets:

        output_filename = os.path.join(project_config.artifacts_folder, f"testssl_{urlparse(t).netloc}_{time.time()}.txt")

        try:
            args = ["testssl.sh", "--openssl", global_config.open_ssl_binary, "--logfile", output_filename, t]

            print(args)
            call(args)

        except Exception as ex:
            print(f"Error writing testssl output to: {output_filename} : {ex}")


@run.command()
def dirb():
    try:
        project_config = VcmProjectConfig()
        project_config.read_project_vcm()
    except ValueError as ex:
        print(ex)
        return

    if not click.confirm('Run dirb against the following targets: %s' % ', '.join(project_config.targets)):
        return

    for t in project_config.targets:
        output_filename = os.path.join(project_config.artifacts_folder,
                                       'dirb_' + str(project_config.targets.index(t))) + '.txt'
        try:
            # dirb url -o output.txt
            args = ["dirb", t, '-o', output_filename]
            call(args)

        except Exception as ex:
            print(f"Error writing dirb output to: {output_filename} : {ex}")


if __name__ == '__main__':
    vcm()
