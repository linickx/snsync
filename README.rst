snsync, like rsync for Simplenote
##################################

snsync is a kinda rsync implementation for Simplenote where your notes can be downloaded (& and uploaded) from plain text files.

.. image:: https://github.com/linickx/snsync/blob/master/docs/snsync_screenshot.gif
        :width: 248px
        :height: 217px
        :align: center

The primary use case is for periodic synchronisation by cron, with all the *useful* output going to a log file and the console output being *pretty* for when humans sync manually.

The configuration file
----------------------

By default, you need `~/.snsync` but the command line options do allow to select another file, the minimal info needed is a username and password::

    [snsync]
    cfg_sn_username = me@here.com
    cfg_sn_password = secret

*IMPORTANT! Protect your .snsync file with the correct permissions and disk encryption*

A few additional options are possible:

* `cfg_nt_path = /Users/linickx/mynotes`  to change the default note path (`~/Simplenote`)
* `cfg_log_path = /Users/Library/Logs/snsync.log` to change the default log path (which is typically within `cfg_nt_path`). Use the keyword `DISABLED` to enable console logging.
* `cfg_log_level = debug` the default logging level is `info`, the brave can change this to `error`, ninja's can enable `debug`

Environment Variables
------------------------

Each of the above configuration options can be over-ridden by environment variables, this is useful if you want to run `snsync` in a container.

* `sn_username` = Simplenote username
* `sn_password` = Simplenote password
* `sn_nt_ext` = Local note file extension (`.txt` by default)
* `sn_nt_path` = Folder path to store local files
* `sn_nt_trashpath` = Folder path for the `trash` directory
* `sn_log_level` = Logging level
* `sn_db_path` = Path for the local .sqllite database
* `sn_log_path` = Path for the local log file


The command line options
------------------------

The following usage/options are available::

    Usage: snsync [OPTIONS]

    OPTIONS:
     -h, --help             Help!
     -d, --dry-run          Dry Run Mode (no changes made/saved)
     -s, --silent           Silent Mode (no std output)
     -D, --download-only    Don't push local changes back/up to Simplenote
     -c, --config=          Config file to read (default: ~/.snsync)

For example: just `snsync` on it's own should work, but something like this can be used for cron: `snsync -s --config=something.txt`

File Deletions
--------------

snsync doesn't delete any files, you can check the source code yourself ;)

When a file is marked for deletion on Simplenote, the local note (*text file*) equivalent is moved to a `.trash` directory. When a file is deleted locally the Simplenote equivalent is marked with Trash tag.

File Conflicts
--------------

If your cron job is very sporadic it possible that a change could be made on the Simplenote server and locally, when this happens the local file is renamed, for example `hello world.txt` would become  `DUP_date_hello world.txt` (*where date is the date/time the file was moved*). Duplicates are then uploaded back into Simplenote for safe keeping.

Local file names are based on the first line of the Simplenote "note". Filenames are generated on a first come, first served basis, for example if you create a Simplenote online with the first line "hello world" then `hello world.txt` will be created, if you create a 2nd note, with completely different contents but the first line is "hello world" then the 2nd file will be called `date_hello world.txt` (*where date is the date/time the file was created*)

File Modifications
------------------

snsync works by maintaining a local sqlite database, typically `.snsycn.sqlite` inside your `cfg_nt_path`. The database maintains a copy of the Simplenote list and a meta table that links Simplenotes to text files.

The script works by comparing the latest Simplenote list to the local cache, and then compares the last modified dates of local files; moves/adds/changes/deletions are then replicated by-directionally. The `--dry-run` option can be used to observe what is going to happen without making any changes.

For those wondering what the log file strings like `agtzaW1wbZRiusssu5sIDAasdfuhas` are; that's the "key" used in the Simplenote cloud to store your note, the local meta database keeps track of those and associates a file name... the cloud don't need no file names dude! ;-)

Large Note Databases
--------------------

The Simplenote API is rate limited, if your note database is large (like mine -> 1,200 notes) then the first full sync will take a long time (mine -> approx 15mins) you will also find a high number of `HTTP ERRORS` reported, just wait and re-run the script, missed notes will be downloaded.

Docker
--------------------

snsync can be run inside a docker container::

    docker run -ti linickx/snsync:latest

This will output snsync, in the normal way with hashes showing the progres. A better way to is to enable console logging (by disabling the log file)::

    docker run -ti -e sn_log_path="DISABLED" linickx/snsync:latest

This will produce a much more docker friendly output.

Containers by default are disposable, therefore you will want to map the `~/Simplenote` directory to something local like::

    docker run -ti -v /home/nick/notes:/root/Simplenote snsync:latest

You will then need to make a decsion on credentials, one option is environment variables ::

    docker run -ti -e sn_username -e sn_password -v /home/nick/notes:/root/Simplenote linickx/snsync:latest

...another option is to mount an snsync config file ::

    docker run -ti -v /home/nick/notes:/root/Simplenote -v /home/nick/.snsync:/root/.snsync linickx/snsync:latest

Finally, docker run is a one-time operation, you can over-ride the entrypoint and use crond to periodically sync your notes. An `example docker-compose <https://github.com/linickx/snsync/blob/master/docs/docker-compose.yml>`_ file can be found in the docs directory, along with `a contab file <https://github.com/linickx/snsync/blob/master/docs/crontab>`_. (Note the example contab runs every 5 mins, that means you have to wait 5mins before anything will happen!)

AoB
---

No warranty is offered, use this at your own risk; I use this for my personal production notes but I always keep backups. The recommended approach is to manually download all your notes for a backup, then use the `--dry-run` option to observe changes until you are happy.

Credz, props and big-ups to https://github.com/insanum/sncli and https://github.com/mrtazz/Simplenote.py as without these opensource projects, snsync would not have got off the ground :)
