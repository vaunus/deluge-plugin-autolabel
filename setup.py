# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 Vaughan Reid <vaunus@gmail.com>
#
# This file is part of AutoLabel and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from setuptools import find_packages, setup

__plugin_name__ = 'AutoLabel'
__author__ = 'Vaughan Reid'
__author_email__ = 'vaunus@gmail.com'
__version__ = '1.0'
__url__ = 'https://github.com/vaunus/deluge-plugin-autolabel'
__license__ = 'GPLv3'
__description__ = 'Automatically assign labels to torrents based on regex pattern matching'
__long_description__ = 'Automatically assign labels to torrents based on regex pattern matching'
__pkg_data__ = {__plugin_name__.lower(): ['data/*']}

setup(
    name=__plugin_name__,
    version=__version__,
    description=__description__,
    author=__author__,
    author_email=__author_email__,
    url=__url__,
    license=__license__,
    zip_safe=False,
    long_description=__long_description__,
    packages=find_packages(),
    package_data=__pkg_data__,
    entry_points="""
    [deluge.plugin.core]
    %s = %s:CorePlugin
    [deluge.plugin.gtk3ui]
    %s = %s:GtkUIPlugin
    [deluge.plugin.web]
    %s = %s:WebUIPlugin
    """
    % ((__plugin_name__, __plugin_name__.lower()) * 3),
)
