# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 Vaughan Reid <vaunus@gmail.com>
#
# This file is part of AutoLabel and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""
AutoLabel GTK UI - Provides the user interface for the AutoLabel plugin.
"""

from __future__ import unicode_literals

import logging

import gi  # isort:skip (Required before Gtk import).

gi.require_version('Gtk', '3.0')  # NOQA: E402

from gi.repository import Gtk

import deluge.component as component
from deluge.plugins.pluginbase import Gtk3PluginBase
from deluge.ui.client import client

from .common import get_resource

log = logging.getLogger(__name__)


class GtkUI(Gtk3PluginBase):
    """GTK UI for the AutoLabel plugin."""

    def enable(self):
        """Called when the plugin is enabled."""
        log.info('AutoLabel GTK UI enabled.')

        self.plugin = component.get('PluginManager')
        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_resource('autolabel_prefs.ui'))

        # Get UI elements
        self.rules_liststore = self.builder.get_object('rules_liststore')
        self.rules_treeview = self.builder.get_object('rules_treeview')
        self.label_entry = self.builder.get_object('label_entry')
        self.pattern_entry = self.builder.get_object('pattern_entry')
        self.enabled_checkbox = self.builder.get_object('enabled_checkbox')
        self.pattern_error_label = self.builder.get_object(
            'pattern_error_label')
        self.apply_on_add_checkbox = self.builder.get_object(
            'apply_on_add_checkbox')
        self.skip_if_labeled_checkbox = self.builder.get_object(
            'skip_if_labeled_checkbox')
        self.case_insensitive_checkbox = self.builder.get_object(
            'case_insensitive_checkbox')

        # Connect signals
        self.builder.get_object('add_rule_button').connect(
            'clicked', self._on_add_rule)
        self.builder.get_object('remove_rule_button').connect(
            'clicked', self._on_remove_rule)
        self.builder.get_object('edit_rule_button').connect(
            'clicked', self._on_edit_rule)
        self.builder.get_object('apply_rules_button').connect(
            'clicked', self._on_apply_rules)
        self.pattern_entry.connect('changed', self._on_pattern_changed)

        # Add preference page
        component.get('Preferences').add_page(
            _('AutoLabel'), self.builder.get_object('autolabel_prefs_box')
        )

        # Setup the context menu for manual label assignment
        self._setup_context_menu()

        # Register hooks
        self.plugin.register_hook('on_apply_prefs', self.on_apply_prefs)
        self.plugin.register_hook('on_show_prefs', self.on_show_prefs)

    def disable(self):
        """Called when the plugin is disabled."""
        log.info('AutoLabel GTK UI disabled.')

        component.get('Preferences').remove_page(_('AutoLabel'))
        self.plugin.deregister_hook('on_apply_prefs', self.on_apply_prefs)
        self.plugin.deregister_hook('on_show_prefs', self.on_show_prefs)

        # Remove context menu
        self._remove_context_menu()

        del self.builder

    def _setup_context_menu(self):
        """Setup the right-click context menu for label assignment."""
        log.debug('Setting up AutoLabel context menu')

        try:
            torrentmenu = component.get('MenuBar').torrentmenu

            # Create a submenu for AutoLabel
            self.menu_item = Gtk.MenuItem(label=_('AutoLabel'))
            self.submenu = Gtk.Menu()
            self.menu_item.set_submenu(self.submenu)

            # Add "Apply Rules" menu item
            self.apply_rules_menuitem = Gtk.MenuItem(label=_('Apply Rules'))
            self.apply_rules_menuitem.connect(
                'activate', self._on_context_apply_rules)
            self.submenu.append(self.apply_rules_menuitem)

            # Add separator
            separator = Gtk.SeparatorMenuItem()
            self.submenu.append(separator)

            # Add "Set Label" submenu
            self.set_label_menuitem = Gtk.MenuItem(label=_('Set Label'))
            self.labels_submenu = Gtk.Menu()
            self.set_label_menuitem.set_submenu(self.labels_submenu)
            self.submenu.append(self.set_label_menuitem)

            self.menu_item.show_all()
            torrentmenu.append(self.menu_item)

            # Register for selection changes to update the labels submenu
            component.get('TorrentView').register_selection_callback(
                self._on_torrent_selection_changed
            )
        except Exception as e:
            log.error(f'Error setting up context menu: {e}')

    def _remove_context_menu(self):
        """Remove the context menu."""
        try:
            if hasattr(self, 'menu_item'):
                component.get('MenuBar').torrentmenu.remove(self.menu_item)
                self.menu_item = None

            component.get('TorrentView').deregister_selection_callback(
                self._on_torrent_selection_changed
            )
        except Exception as e:
            log.error(f'Error removing context menu: {e}')

    def _on_torrent_selection_changed(self, torrent_ids):
        """Update the labels submenu when torrent selection changes."""
        if not hasattr(self, 'menu_item'):
            return

        self.menu_item.set_sensitive(bool(torrent_ids))

        if torrent_ids:
            # Refresh the labels submenu
            self._refresh_labels_submenu()

    def _refresh_labels_submenu(self):
        """Refresh the labels submenu with available labels."""
        # Clear existing items
        for child in self.labels_submenu.get_children():
            self.labels_submenu.remove(child)

        def on_get_labels(labels):
            # Add "No Label" option
            no_label_item = Gtk.MenuItem(label=_('No Label'))
            no_label_item.connect('activate', lambda w: self._on_set_label(''))
            self.labels_submenu.append(no_label_item)

            if labels:
                separator = Gtk.SeparatorMenuItem()
                self.labels_submenu.append(separator)

                for label in sorted(labels):
                    label_item = Gtk.MenuItem(label=label)
                    label_item.connect('activate', lambda w,
                                       l=label: self._on_set_label(l))
                    self.labels_submenu.append(label_item)

            self.labels_submenu.show_all()

        client.autolabel.get_available_labels().addCallback(on_get_labels)

    def _on_set_label(self, label):
        """Set the label for selected torrents."""
        selected = component.get('TorrentView').get_selected_torrents()
        for torrent_id in selected:
            log.info(
                f'AutoLabel: Setting label "{label}" for torrent {torrent_id}')
            if label:
                client.autolabel.set_torrent_label(torrent_id, label)
            else:
                # Remove label by setting empty string
                client.autolabel.set_torrent_label(torrent_id, '')

    def _on_context_apply_rules(self, widget):
        """Apply rules to selected torrents from context menu."""
        selected = component.get('TorrentView').get_selected_torrents()
        for torrent_id in selected:
            log.info(f'AutoLabel: Applying rules to torrent {torrent_id}')
            client.autolabel.apply_rules_to_torrent(torrent_id)

    def _on_pattern_changed(self, entry):
        """Validate the regex pattern as the user types."""
        pattern = entry.get_text()
        if not pattern:
            self.pattern_error_label.set_text('')
            return

        def on_validate(result):
            if result.get('valid'):
                self.pattern_error_label.set_text('')
                entry.get_style_context().remove_class('error')
            else:
                self.pattern_error_label.set_text(
                    result.get('error', 'Invalid regex'))
                entry.get_style_context().add_class('error')

        client.autolabel.validate_regex(pattern).addCallback(on_validate)

    def _on_add_rule(self, button):
        """Add a new rule."""
        label = self.label_entry.get_text().strip()
        pattern = self.pattern_entry.get_text().strip()
        enabled = self.enabled_checkbox.get_active()

        if not label or not pattern:
            return

        def on_add_result(result):
            if result.get('success'):
                # Add to liststore
                self.rules_liststore.append([enabled, label, pattern])
                # Clear inputs
                self.label_entry.set_text('')
                self.pattern_entry.set_text('')
                self.enabled_checkbox.set_active(True)
            else:
                self.pattern_error_label.set_text(
                    result.get('error', 'Error adding rule'))

        client.autolabel.add_rule(
            label, pattern, enabled).addCallback(on_add_result)

    def _on_remove_rule(self, button):
        """Remove the selected rule."""
        selection = self.rules_treeview.get_selection()
        model, tree_iter = selection.get_selected()

        if tree_iter:
            path = model.get_path(tree_iter)
            index = path.get_indices()[0]

            def on_remove_result(result):
                if result.get('success'):
                    model.remove(tree_iter)

            client.autolabel.remove_rule(index).addCallback(on_remove_result)

    def _on_edit_rule(self, button):
        """Edit the selected rule."""
        selection = self.rules_treeview.get_selection()
        model, tree_iter = selection.get_selected()

        if tree_iter:
            # Populate the entry fields with the selected rule
            enabled = model.get_value(tree_iter, 0)
            label = model.get_value(tree_iter, 1)
            pattern = model.get_value(tree_iter, 2)

            self.enabled_checkbox.set_active(enabled)
            self.label_entry.set_text(label)
            self.pattern_entry.set_text(pattern)

            # Remove the rule (will be re-added when user clicks Add)
            path = model.get_path(tree_iter)
            index = path.get_indices()[0]

            def on_remove_result(result):
                if result.get('success'):
                    model.remove(tree_iter)

            client.autolabel.remove_rule(index).addCallback(on_remove_result)

    def _on_apply_rules(self, button):
        """Apply rules to all torrents."""
        def on_result(result):
            if result.get('success'):
                log.info(
                    f"AutoLabel: Applied labels to {result.get('labeled_count', 0)} torrents")

        client.autolabel.apply_rules_to_all().addCallback(on_result)

    def on_apply_prefs(self):
        """Called when preferences are applied."""
        log.debug('AutoLabel: Applying preferences')

        config = {
            'apply_on_add': self.apply_on_add_checkbox.get_active(),
            'skip_if_labeled': self.skip_if_labeled_checkbox.get_active(),
            'case_insensitive': self.case_insensitive_checkbox.get_active(),
        }

        client.autolabel.set_config(config)

    def on_show_prefs(self):
        """Called when preferences are shown."""
        log.debug('AutoLabel: Showing preferences')

        def on_get_config(config):
            self.apply_on_add_checkbox.set_active(
                config.get('apply_on_add', True))
            self.skip_if_labeled_checkbox.set_active(
                config.get('skip_if_labeled', True))
            self.case_insensitive_checkbox.set_active(
                config.get('case_insensitive', True))

            # Load rules
            self.rules_liststore.clear()
            for rule in config.get('rules', []):
                self.rules_liststore.append([
                    rule.get('enabled', True),
                    rule.get('label', ''),
                    rule.get('pattern', '')
                ])

        client.autolabel.get_config().addCallback(on_get_config)
