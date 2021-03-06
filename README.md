# vcm
very complete management (a pentest tool for organizing things)

## Settings storage
Global settings are stored in ~/.vcm by default.

Project settings are stored in ./.vcm in the project directory

## Project Management & File Syncing
* vcm create - creates a project folder with appropriate subfolders and project settings
* vcm pull - rsyncs from a remote folder to the local project folder
* vcm push - rsyncs to a remote folder from the local project folder

## Tool Execution & Artifact Storage
Filenames have an epoch time suffix for historical versioning 
* vcm run nmap - uses default arguments -sV -p-
* vcm run nikto 
* vcm run testssl - uses /usr/bin/openssl as the default but can be overridden in global settings
* vcm run dirb - uses the default wordlist

## Installation
* Make vcm.py executable
* Copy to path
* Run vcm create to create a new project directory and configuration file
* Run commands from within projects directory

## Dependencies
* Python 3.6.8
* rsync
* openssl binary (change location in the code)
* testssl (brew install testssl)
* nmap (brew install nmap)
* python modules (pip install -r requirements.txt)
