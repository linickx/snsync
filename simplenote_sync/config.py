"""
    Configuration settings for snsync
"""
# pylint: disable=W0702
# pylint: disable=C0301

import os
import collections
import configparser

class Config:
    """
        Config Object
    """

    def __init__(self, custom_file=None):
        """
            Defult settings and the like.
        """
        self.home = os.path.abspath(os.path.expanduser('~'))
        # Static Defaults
        defaults = \
        {
            'cfg_sn_username'       : '',
            'cfg_sn_password'       : '',
            'cfg_nt_ext'       : 'txt',
            'cfg_nt_path'       : os.path.join(self.home, 'Simplenote'),
            'cfg_nt_trashpath'       : '.trash',
            'cfg_nt_filenamelen'       : '60',
            'cfg_log_level'       : 'info'
        }

        cp = configparser.SafeConfigParser(defaults)
        if custom_file is not None:
            self.configs_read = cp.read([custom_file])
        else:
            self.configs_read = cp.read([os.path.join(self.home, '.snsync')])

        cfg_sec = 'snsync'

        if not cp.has_section(cfg_sec):
            cp.add_section(cfg_sec)

        self.configs = collections.OrderedDict()

        #
        #    Environment Varialbles over-ride config file settings.
        #    Config files are cfg_abc
        #    Envs are sn_abc
        #

        if os.environ.get('sn_username') is None:
            val_sn_username = cp.get(cfg_sec, 'cfg_sn_username', raw=True)
        else:
            val_sn_username = os.environ.get('sn_username')
        self.configs['sn_username'] = [val_sn_username, 'Simplenote Username']

        if os.environ.get('sn_password') is None:
            val_sn_passowrd = cp.get(cfg_sec, 'cfg_sn_password', raw=True)
        else:
            val_sn_passowrd = os.environ.get('sn_password')
        self.configs['sn_password'] = [val_sn_passowrd, 'Simplenote Password']

        if os.environ.get('sn_nt_ext') is None:
            val_sn_nt_ext = cp.get(cfg_sec, 'cfg_nt_ext')
        else:
            val_sn_nt_ext = os.environ.get('sn_nt_ext')
        self.configs['cfg_nt_ext'] = [val_sn_nt_ext, 'Note file extension']

        if os.environ.get('sn_nt_path') is None:
            val_sn_nt_path = cp.get(cfg_sec, 'cfg_nt_path')
        else:
            val_sn_nt_path = os.environ.get('sn_nt_path')
        self.configs['cfg_nt_path'] = [val_sn_nt_path, 'Note storage path']

        if os.environ.get('sn_nt_trashpath') is None:
            val_sn_nt_trashpath = cp.get(cfg_sec, 'cfg_nt_trashpath')
        else:
            val_sn_nt_trashpath = os.environ.get('sn_nt_trashpath')
        self.configs['cfg_nt_trashpath'] = [val_sn_nt_trashpath, 'Note Trash Bin Folder for deleted notes']

        if os.environ.get('sn_nt_filenamelen') is None:
            val_sn_nt_filenamelen = cp.get(cfg_sec, 'cfg_nt_filenamelen')
        else:
            val_sn_nt_filenamelen = os.environ.get('sn_nt_filenamelen')
        self.configs['cfg_nt_filenamelen'] = [val_sn_nt_filenamelen, 'Length of Filename']

        if os.environ.get('sn_log_level') is None:
            val_sn_log_level = cp.get(cfg_sec, 'cfg_log_level')
        else:
            val_sn_log_level = os.environ.get('sn_log_level')
        self.configs['cfg_log_level'] = [val_sn_log_level, 'snsync log level']

        # Dynamic Defaults
        if os.environ.get('sn_db_path') is None:
            if cp.has_option(cfg_sec, 'cfg_db_path'):
                val_sn_db_path = cp.get(cfg_sec, 'cfg_db_path')
            else:
                val_sn_db_path = os.path.join(cp.get(cfg_sec, 'cfg_nt_path'), '.snsync.sqlite')
        else:
            val_sn_db_path = os.environ.get('sn_db_path')
        self.configs['cfg_db_path'] = [val_sn_db_path, 'snsync database location']

        if os.environ.get('sn_log_path') is None:
            if cp.has_option(cfg_sec, 'cfg_log_path'):
                val_sn_log_path = cp.get(cfg_sec, 'cfg_log_path')
            else:
                val_sn_log_path = os.path.join(cp.get(cfg_sec, 'cfg_nt_path'), '.snsync.log')
        else:
            val_sn_log_level = os.environ.get('sn_log_path')
        self.configs['cfg_log_path'] = [val_sn_log_path, 'snsync log location']


    def get_config(self, name):
        """
            Return a config setting
        """
        return self.configs[name][0]

    def get_config_descr(self, name):
        """
            Return a config description (future use in docs)
        """
        return self.configs[name][1]
