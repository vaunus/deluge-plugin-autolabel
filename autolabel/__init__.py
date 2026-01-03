# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 Vaughan Reid <vaunus@gmail.com>
#
# This file is part of AutoLabel and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""
AutoLabel - Automatic Label Assignment for Deluge

This plugin automatically assigns labels to torrents based on regex pattern
matching of torrent names. It integrates with Deluge's native Label plugin.
"""

from __future__ import unicode_literals

from deluge.plugins.init import PluginInitBase


class CorePlugin(PluginInitBase):
    def __init__(self, plugin_name):
        from .core import Core as _pluginCls

        self._plugin_cls = _pluginCls
        super(CorePlugin, self).__init__(plugin_name)


class GtkUIPlugin(PluginInitBase):
    def __init__(self, plugin_name):
        from .gtkui import GtkUI as _pluginCls

        self._plugin_cls = _pluginCls
        super(GtkUIPlugin, self).__init__(plugin_name)


class WebUIPlugin(PluginInitBase):
    def __init__(self, plugin_name):
        from .webui import WebUI as _pluginCls

        self._plugin_cls = _pluginCls
        super(WebUIPlugin, self).__init__(plugin_name)
