
import os
from urllib.request import urlopen

def download_update(version):
    print(f'Updating to version {version}')
    # updater.py
    with urlopen('https://raw.githubusercontent.com/kianbennett/MarsRoverViewer/main/updater.py') as file:
        content = file.read().decode()
        with open('updater.py', 'w') as download:
            download.write(content)
    # main.py
    with urlopen('https://raw.githubusercontent.com/kianbennett/MarsRoverViewer/main/main.py') as file:
        content = file.read().decode()
        with open('main.py', 'w') as download:
            download.write(content)
    # version file
    version_file = open("version", "w")
    version_file.write(str(version))
    version_file.close()

local_version = 0.0

# Read local version
if os.path.exists('version'):
    with open('version', 'r') as file:
        content = file.read().strip()
        local_version = float(content)
        print(f'Local version: {local_version}')
else:
    print('Local version could not be identified')

url_remote_version = "https://raw.githubusercontent.com/kianbennett/MarsRoverViewer/main/version"

print('Checking remote version at ' + url_remote_version)

# Read remote version
with urlopen(url_remote_version) as file:
    content = file.read().decode()
    remote_version = float(content)
    print(f'Remote version: {remote_version}')
    if(remote_version != local_version):
        download_update(remote_version)
    else:
        print('Up to date')
