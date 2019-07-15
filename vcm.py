#!/usr/bin/env python

import click
import os
from pipes import quote
import ConfigParser
from subprocess import call
import subprocess
from urlparse import urlparse
import re

# Settings (TODO: Move this to a global config file.)
OPENSSL_BINARY = "/Users/wriggins/openssl/openssl.Darwin.x86_64"

# Stuff to automate later:
# * brew install testssl
# * download openssl binary and store it in default location
# * brew install nmap
# * brew install nikto

@click.group()
def vcm():
    pass

###
#   Folder and project management
###
@vcm.command()
def create():
    # create a config file .vcm and ask for: project name, root dir name, remote directory, urls (csv)
    project_name = click.prompt('Project Name', type=str)
    local_folder = click.prompt('Local Path', type=str, default=os.path.join(os.getcwd(), project_name))
    remote_folder = click.prompt('Remote Path', type=str)
    url_targets = click.prompt('URL Targets (CSV)', type=str)
    # create path if not exists
    if not os.path.exists(local_folder):
        try:
            os.makedirs(local_folder)
        except:
            print "Error creating local folder: %s" % local_folder
            return
    # create logistics, artifacts, and reports directories
    for folder in ['reports', 'artifacts', 'logistics']:
        if not os.path.exists(os.path.join(local_folder, folder)):
            try:
                os.makedirs(os.path.join(local_folder, folder))
            except:
                print "Error creating subfolder: %s" % os.path.join(local_folder, folder)
                return
    # write config file to .vcm in the root
    my_config = ConfigParser.RawConfigParser()
    my_config.add_section('ProjectSettings')
    my_config.set('ProjectSettings', 'project_name', project_name)
    my_config.set('ProjectSettings', 'local_path', os.path.join(local_folder, ''))
    my_config.set('ProjectSettings', 'remote_path', os.path.join(remote_folder, ''))
    my_config.set('ProjectSettings', 'url_targets', url_targets)
    with open(os.path.join(local_folder, '.vcm'), 'wb') as configfile:
        try:
            my_config.write(configfile)
        except:
            print "Error writing config file: %s" % os.path.join(local_folder, '.vcm')
            return


@vcm.command()
def push():
    # ensure the remote dir is mounted
    read_config = ConfigParser.RawConfigParser()

    cf = read_config.read('.vcm')

    if len(cf) == 0:
        print "Unable to read config file: %s" % os.path.join(os.getcwd(), '.vcm')
        return

    remote_folder = read_config.get('ProjectSettings', 'remote_path')
    local_folder = read_config.get('ProjectSettings', 'local_path')

    # do an rsync -ah from local to remote
    if click.confirm('Sync local (%s) to remote (%s)?' % (local_folder, remote_folder)):
        args = ["rsync", "-ah", "--progress", local_folder, remote_folder]
        call(args)


@vcm.command()
def pull():
    # ensure the remote dir is mounted
    # do an rsync -ah from remote to local
    read_config = ConfigParser.RawConfigParser()

    cf = read_config.read('.vcm')

    if len(cf) == 0:
        print "Unable to read config file: %s" % os.path.join(os.getcwd(), '.vcm')
        return

    remote_folder = read_config.get('ProjectSettings', 'remote_path')
    local_folder = read_config.get('ProjectSettings', 'local_path')

    # do an rsync -ah from local to remote
    if click.confirm('Sync remote (%s) to local (%s)?' % (remote_folder, local_folder)):
        args = ["rsync", "-ah", "--progress", remote_folder, local_folder]
        call(args)

###
#   Running testing tools
###
@vcm.group()
def run():
    pass

@run.command()
def nmap():
    # check if url .vcm setting is set and is valid csv first; strip protocol if exists
    read_config = ConfigParser.RawConfigParser()

    cf = read_config.read('.vcm')

    if len(cf) == 0:
        print "Unable to read config file: %s" % os.path.join(os.getcwd(), '.vcm')
        return

    local_folder = read_config.get('ProjectSettings', 'local_path')
    url_targets = re.split(",\s?", read_config.get('ProjectSettings', 'url_targets'))

    targets = []
    for t in url_targets:
        targets.append(urlparse(t).netloc)

    print "Please note, this will only work if the url targets have been set to a comma delimited set of URLs with scheme."
    if click.confirm('Run nmap against the following targets: %s' % ', '.join(targets)):
        args = ["nmap", "-sV", "-p-"]
        for t in targets:
            args.append(t)
        args.append("-oA")
        args.append(os.path.join(local_folder, 'artifacts', 'nmap'))
        call(args)
    else:
        pass


## FIX THIS TO ITERATE OVER URLS LIKE DIRB DOES
@run.command()
def nikto():
    # check if url .vcm setting is set and is valid csv first
    read_config = ConfigParser.RawConfigParser()

    cf = read_config.read('.vcm')

    if len(cf) == 0:
        print "Unable to read config file: %s" % os.path.join(os.getcwd(), '.vcm')
        return

    local_folder = read_config.get('ProjectSettings', 'local_path')
    url_targets = re.split(",\s?", read_config.get('ProjectSettings', 'url_targets'))

    print "Please note, this will only work if the url targets have been set to a comma delimited set of URLs with scheme."
    if click.confirm('Run nikto against the following targets: %s' % ', '.join(url_targets)):
        try:
            # nikto -h https://www.test.com -ssl -Format html -output .
            filename = os.path.join(local_folder, 'artifacts', 'nikto')
            args = ["nikto", "-h"]
            for t in url_targets:
                args.append(t+',')
            args.append('-ssl')
            args.append('-Format')
            args.append('html')
            args.append('-output')
            args.append(os.path.join(local_folder, 'artifacts', 'nikto'))
            print args
            call(args)
        except:
            print "Error writing nikto output to: %s" % filename
    else:
        pass


@run.command()
def testssl():
    # check if url .vcm setting is set and is valid csv first
    read_config = ConfigParser.RawConfigParser()

    cf = read_config.read('.vcm')

    if len(cf) == 0:
        print "Unable to read config file: %s" % os.path.join(os.getcwd(), '.vcm')
        return

    local_folder = read_config.get('ProjectSettings', 'local_path')
    url_targets = re.split(",\s?", read_config.get('ProjectSettings', 'url_targets'))

    targets = []
    for t in url_targets:
        targets.append('https://'+urlparse(t).netloc)

    print "Please note, this will only work if the url targets have been set to a comma delimited set of URLs with scheme."
    if click.confirm('Run testssl against the following targets: %s' % ', '.join(targets)):
        for t in targets:
            try:
                filename = os.path.join(local_folder, 'artifacts', 'testssl_'+str(targets.index(t)))+'.html'
                with open(filename, 'w') as f:
                    args_testssl = ["testssl.sh", "--openssl", OPENSSL_BINARY, t]
                    testssl = subprocess.Popen(args_testssl, stdout=subprocess.PIPE)
                    aha = subprocess.Popen(["aha"], stdin=testssl.stdout, stdout=f)
                    aha.wait()
            except:
                print "Error writing testssl output to: %s" % filename
    else:
        pass


@run.command()
def dirb():
    # check if url .vcm setting is set and is valid csv first
    read_config = ConfigParser.RawConfigParser()

    cf = read_config.read('.vcm')

    if len(cf) == 0:
        print "Unable to read config file: %s" % os.path.join(os.getcwd(), '.vcm')
        return

    local_folder = read_config.get('ProjectSettings', 'local_path')
    url_targets = re.split(",\s?", read_config.get('ProjectSettings', 'url_targets'))

    targets = []
    for t in url_targets:
        targets.append(t)

    print "Please note, this will only work if the url targets have been set to a comma delimited set of URLs with scheme."
    if click.confirm('Run dirb against the following targets: %s' % ', '.join(targets)):
        for t in targets:
            try:
                # dirb url -o output.txt
                filename = os.path.join(local_folder, 'artifacts', 'dirb_'+str(targets.index(t)))+'.txt'
                args = ["dirb", t]
                args.append('-o')
                args.append(filename)
                print args
                call(args)
            except:
                print "Error writing dirb output to: %s" % filename
    else:
        pass

if __name__ == '__main__':
    vcm()
