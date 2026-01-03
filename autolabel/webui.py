# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 Vaughan Reid <vaunus@gmail.com>
#
# This file is part of AutoLabel and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""
AutoLabel Web UI - Web interface for AutoLabel plugin.
"""

from __future__ import unicode_literals

import logging

from deluge.plugins.pluginbase import WebPluginBase

from .common import get_resource

log = logging.getLogger(__name__)


class WebUI(WebPluginBase):
    """
    Web UI for the AutoLabel plugin.

    Provides a preferences page for configuring auto-labeling rules.
    """

    scripts = [get_resource('autolabel.js')]
    debug_scripts = scripts

    def enable(self):
        """Called when the plugin is enabled."""
        log.info('AutoLabel Web UI enabled.')

    def disable(self):
        """Called when the plugin is disabled."""
        log.info('AutoLabel Web UI disabled.')
