# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 Vaughan Reid <vaunus@gmail.com>
#
# This file is part of AutoLabel and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""
AutoLabel Core - Handles regex pattern matching and label assignment.
"""

from __future__ import unicode_literals

import logging
import re

import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export
from deluge.plugins.pluginbase import CorePluginBase

log = logging.getLogger(__name__)

# Default configuration
DEFAULT_PREFS = {
    # List of rules: [{'label': 'label_name', 'pattern': 'regex_pattern', 'enabled': True}, ...]
    'rules': [],
    # Whether to apply rules on torrent add
    'apply_on_add': True,
    # Whether to skip torrents that already have a label
    'skip_if_labeled': True,
    # Case-insensitive matching by default
    'case_insensitive': True,
}


class Core(CorePluginBase):
    """
    Core plugin class for AutoLabel.

    Handles regex pattern matching and integration with the Label plugin.
    """

    def __init__(self, plugin_name):
        super().__init__(plugin_name)
        self.config = None
        self.label_plugin = None

    def enable(self):
        """Called when the plugin is enabled."""
        log.info('AutoLabel plugin enabled.')

        self.config = deluge.configmanager.ConfigManager(
            'autolabel.conf', DEFAULT_PREFS
        )

        # Register event handlers
        component.get('EventManager').register_event_handler(
            'TorrentAddedEvent', self._on_torrent_added
        )

        log.debug('AutoLabel: Registered event handlers.')

    def disable(self):
        """Called when the plugin is disabled."""
        log.info('AutoLabel plugin disabled.')

        # Deregister event handlers
        try:
            component.get('EventManager').deregister_event_handler(
                'TorrentAddedEvent', self._on_torrent_added
            )
        except Exception as e:
            log.warning(f'Error deregistering event handler: {e}')

    def update(self):
        """Called periodically by Deluge."""
        pass

    def _get_label_plugin(self):
        """Get a reference to the Label plugin core."""
        try:
            # Try to get the Label plugin from the plugin manager
            plugin_manager = component.get('CorePluginManager')
            if 'Label' in plugin_manager.get_enabled_plugins():
                # Access the Label plugin's core
                # The plugin manager stores PluginInitBase instances,
                # which have a .plugin attribute containing the actual Core class
                label_obj = plugin_manager.plugins.get('Label')
                if label_obj and hasattr(label_obj, 'plugin'):
                    return label_obj.plugin
                else:
                    log.error('Label plugin found but has unexpected structure')
                    return label_obj
            else:
                log.error(
                    'Label plugin is not enabled. Please enable it in Preferences > Plugins')
        except Exception as e:
            log.error(f'Could not get Label plugin: {e}')
        return None

    def _get_torrent_name(self, torrent_id):
        """Get the name of a torrent by its ID."""
        try:
            torrent_manager = component.get('TorrentManager')
            if torrent_id in torrent_manager.torrents:
                torrent = torrent_manager.torrents[torrent_id]
                status = torrent.get_status(['name'])
                return status.get('name', '')
        except Exception as e:
            log.error(f'Error getting torrent name: {e}')
        return ''

    def _get_torrent_label(self, torrent_id):
        """Get the current label of a torrent."""
        try:
            label_config = deluge.configmanager.ConfigManager(
                'label.conf', defaults=False)
            if 'torrent_labels' in label_config:
                return label_config['torrent_labels'].get(torrent_id, '')
        except Exception as e:
            log.debug(f'Error getting torrent label: {e}')
        return ''

    def _set_torrent_label(self, torrent_id, label_id):
        """Set the label for a torrent using the Label plugin."""
        try:
            label_plugin = self._get_label_plugin()
            if label_plugin:
                # Ensure the label exists
                existing_labels = label_plugin.get_labels()
                if label_id.lower() not in [l.lower() for l in existing_labels]:
                    log.info(f'AutoLabel: Creating new label "{label_id}"')
                    try:
                        label_plugin.add(label_id.lower())
                    except Exception as e:
                        log.warning(
                            f'Could not create label "{label_id}": {e}')
                        return False

                # Set the torrent's label
                label_plugin.set_torrent(torrent_id, label_id.lower())
                log.info(
                    f'AutoLabel: Set label "{label_id}" for torrent {torrent_id}')
                return True
            else:
                log.warning('AutoLabel: Label plugin not available')
        except Exception as e:
            log.error(f'Error setting torrent label: {e}')
        return False

    def _match_pattern(self, torrent_name, pattern):
        """Check if a torrent name matches a regex pattern."""
        try:
            flags = re.IGNORECASE if self.config['case_insensitive'] else 0
            return bool(re.search(pattern, torrent_name, flags))
        except re.error as e:
            log.error(f'Invalid regex pattern "{pattern}": {e}')
            return False

    def _on_torrent_added(self, torrent_id, from_state):
        """Called when a torrent is added."""
        if from_state:
            # Don't process torrents loaded from state (on startup)
            return

        if not self.config['apply_on_add']:
            return

        self._apply_rules_to_torrent(torrent_id)

    def _apply_rules_to_torrent(self, torrent_id):
        """Apply all enabled rules to a single torrent."""
        torrent_name = self._get_torrent_name(torrent_id)
        if not torrent_name:
            log.warning(
                f'AutoLabel: Could not get name for torrent {torrent_id}')
            return False

        # Check if torrent already has a label
        if self.config['skip_if_labeled']:
            current_label = self._get_torrent_label(torrent_id)
            if current_label:
                log.debug(
                    f'AutoLabel: Torrent already labeled as "{current_label}", skipping')
                return False

        # Check each rule
        for rule in self.config['rules']:
            if not rule.get('enabled', True):
                continue

            pattern = rule.get('pattern', '')
            label = rule.get('label', '')

            if not pattern or not label:
                continue

            if self._match_pattern(torrent_name, pattern):
                log.info(
                    f'AutoLabel: Torrent "{torrent_name}" matched pattern "{pattern}"')
                return self._set_torrent_label(torrent_id, label)

        return False

    @export
    def set_config(self, config):
        """Set the plugin configuration."""
        for key in config:
            self.config[key] = config[key]
        self.config.save()
        log.debug('AutoLabel: Configuration saved')

    @export
    def get_config(self):
        """Get the plugin configuration."""
        return self.config.config

    @export
    def add_rule(self, label, pattern, enabled=True):
        """Add a new label-regex rule."""
        # Validate the regex pattern
        try:
            re.compile(pattern)
        except re.error as e:
            log.error(f'Invalid regex pattern: {e}')
            return {'success': False, 'error': str(e)}

        rule = {
            'label': label,
            'pattern': pattern,
            'enabled': enabled
        }
        self.config['rules'].append(rule)
        self.config.save()
        log.info(
            f'AutoLabel: Added rule - Label: "{label}", Pattern: "{pattern}"')
        return {'success': True, 'rule_index': len(self.config['rules']) - 1}

    @export
    def remove_rule(self, index):
        """Remove a rule by its index."""
        try:
            if 0 <= index < len(self.config['rules']):
                removed = self.config['rules'].pop(index)
                self.config.save()
                log.info(f'AutoLabel: Removed rule at index {index}')
                return {'success': True, 'removed': removed}
            else:
                return {'success': False, 'error': 'Invalid index'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @export
    def update_rule(self, index, label=None, pattern=None, enabled=None):
        """Update an existing rule."""
        try:
            if 0 <= index < len(self.config['rules']):
                rule = self.config['rules'][index]

                if pattern is not None:
                    # Validate the regex pattern
                    try:
                        re.compile(pattern)
                    except re.error as e:
                        return {'success': False, 'error': f'Invalid regex: {e}'}
                    rule['pattern'] = pattern

                if label is not None:
                    rule['label'] = label

                if enabled is not None:
                    rule['enabled'] = enabled

                self.config.save()
                log.info(f'AutoLabel: Updated rule at index {index}')
                return {'success': True, 'rule': rule}
            else:
                return {'success': False, 'error': 'Invalid index'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @export
    def get_rules(self):
        """Get all rules."""
        return self.config['rules']

    @export
    def validate_regex(self, pattern):
        """Validate a regex pattern."""
        try:
            re.compile(pattern)
            return {'valid': True}
        except re.error as e:
            return {'valid': False, 'error': str(e)}

    @export
    def apply_rules_to_torrent(self, torrent_id):
        """Manually apply rules to a specific torrent."""
        return self._apply_rules_to_torrent(torrent_id)

    @export
    def apply_rules_to_all(self):
        """Apply rules to all existing torrents."""
        try:
            torrent_manager = component.get('TorrentManager')
            count = 0
            for torrent_id in torrent_manager.torrents:
                if self._apply_rules_to_torrent(torrent_id):
                    count += 1
            log.info(f'AutoLabel: Applied labels to {count} torrents')
            return {'success': True, 'labeled_count': count}
        except Exception as e:
            log.error(f'Error applying rules to all torrents: {e}')
            return {'success': False, 'error': str(e)}

    @export
    def set_torrent_label(self, torrent_id, label):
        """Manually set the label for a torrent."""
        return self._set_torrent_label(torrent_id, label)

    @export
    def get_available_labels(self):
        """Get all available labels from the Label plugin."""
        try:
            label_plugin = self._get_label_plugin()
            if label_plugin:
                return label_plugin.get_labels()
        except Exception as e:
            log.error(f'Error getting available labels: {e}')
        return []

    @export
    def test_pattern(self, pattern, test_string):
        """Test a regex pattern against a string."""
        try:
            flags = re.IGNORECASE if self.config['case_insensitive'] else 0
            match = re.search(pattern, test_string, flags)
            if match:
                return {
                    'matches': True,
                    'matched_text': match.group(0),
                    'start': match.start(),
                    'end': match.end()
                }
            return {'matches': False}
        except re.error as e:
            return {'matches': False, 'error': str(e)}
