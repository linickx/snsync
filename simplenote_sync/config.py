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
        self.configs['sn_username'] = [cp.get(cfg_sec, 'cfg_sn_username', raw=True), 'Simplenote Username']
        self.configs['sn_password'] = [cp.get(cfg_sec, 'cfg_sn_password', raw=True), 'Simplenote Password']
        self.configs['cfg_nt_ext'] = [cp.get(cfg_sec, 'cfg_nt_ext'), 'Note file extension']
        self.configs['cfg_nt_path'] = [cp.get(cfg_sec, 'cfg_nt_path'), 'Note storage path']
        self.configs['cfg_nt_trashpath'] = [cp.get(cfg_sec, 'cfg_nt_trashpath'), 'Note Trash Bin Folder for deleted notes']
        self.configs['cfg_nt_filenamelen'] = [cp.get(cfg_sec, 'cfg_nt_filenamelen'), 'Length of Filename']
        self.configs['cfg_log_level'] = [cp.get(cfg_sec, 'cfg_log_level'), 'snsync log level']

        # Dynamic Defaults
        if cp.has_option(cfg_sec, 'cfg_db_path'):
            self.configs['cfg_db_path'] = [cp.get(cfg_sec, 'cfg_db_path'), 'snsync database location']
        else:
            self.configs['cfg_db_path'] = [os.path.join(cp.get(cfg_sec, 'cfg_nt_path'), '.snsync.sqlite'), 'snsync database location']

        if cp.has_option(cfg_sec, 'cfg_log_path'):
            self.configs['cfg_log_path'] = [cp.get(cfg_sec, 'cfg_log_path'), 'snsync log location']
        else:
            self.configs['cfg_log_path'] = [os.path.join(cp.get(cfg_sec, 'cfg_nt_path'), '.snsync.log'), 'snsync log location']

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
