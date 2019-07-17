# vcm
very complete management (a pentest tool for organizing things)

## Project Management & File Syncing
* vcm create
* vcm pull
* vcm push

## Tool Execution & Artifact Storage
* vcm run nmap
* vcm run nikto
* vcm run testssl
* vcm run dirb

## Installation
* Make vcm.py executable
* Copy to path
* Run commands (except `create`) from within projects directory

## Dependencies
* Python 3.6.8
* rsync
* openssl binary (change location in the code)
* testssl (brew install testssl)
* nmap (brew install nmap)
* python modules (pip install -r requirements.txt)
