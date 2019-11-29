# Mattermost channel deleter

When an Channel is deleted in Mattermost over the API, its only marked as deleted in the DB (which means effectively disabled and not deleted). The messages and all users are still preserved.

Mattermost currently (2019-09) does not offer the possibility to delete channels via the API, this is only possible via the Mattermost CLI-Tool (`mattermost channel delete <USER>`).

This Script which runs on a Mattermost-Node first checks the Mattermost database for disabled channels, and if they are deleted and prefixed with `deleted-` it will permanently remove them.

The Script uses Mattermost-Config for connecting to the database.


## Installation

### Script Installation

Prerequisites:
- EPEL Repository activated

Procedure:
- Install requirements:
```
yum install install mysql-connector-python python-setuptools
```
- Install the Script:
```
git clone https://github.com/adfinis-sygroup/mattermost-channel-deleter
cd mattermost-channel-deleter
python setup.py install
```

### Activate Mattermost User deleter timer

```
systemctl enable mattermost-channel-deleter.timer
```

## Usage

```
usage: mattermost-channel-deleter [-h] --config CONFIG --mattermost-root
                               MATTERMOST_ROOT [--dry-run] [--debug]
```

- `--config` path to Mattermost `config.json` (normally `/opt/mattermost/config/config.json`)
- `--mattermost-root` path to Mattermost install root (normally `/opt/mattermost`)
- `--debug` is a flag to display debug output
- `--dry-run` if this flag is specified, only show what the script would delete instead of actually deleting the users

## License

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the Free
Software Foundation, version 3 of the License.

## Copyright

Copyright (c) 2019 [Adfinis SyGroup AG](https://adfinis-sygroup.ch)
