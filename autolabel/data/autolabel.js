/**
 * autolabel.js
 *
 * Copyright (C) 2024 Vaughan Reid <vaunus@gmail.com>
 *
 * This file is part of AutoLabel and is licensed under GNU General Public License 3.0, or later.
 */

Ext.ns("Deluge.ux.preferences");

/**
 * @class Deluge.ux.preferences.AutoLabelPage
 * @extends Ext.Panel
 */
Deluge.ux.preferences.AutoLabelPage = Ext.extend(Ext.Panel, {
  title: _("AutoLabel"),
  header: false,
  border: false,
  layout: "fit",
  autoScroll: true,

  initComponent: function () {
    // Create the rules grid store
    this.rulesStore = new Ext.data.JsonStore({
      autoDestroy: true,
      fields: ["label", "pattern"],
    });

    // Create the checkbox
    this.caseInsensitiveCheckbox = new Ext.form.Checkbox({
      boxLabel: _("Case-insensitive matching"),
      name: "case_insensitive",
      hideLabel: true,
      checked: true,
    });

    // Create the rules grid
    this.rulesGrid = new Ext.grid.EditorGridPanel({
      store: this.rulesStore,
      columns: [
        {
          header: _("Label"),
          dataIndex: "label",
          width: 120,
          editor: new Ext.form.TextField(),
        },
        {
          header: _("Pattern (Regex)"),
          dataIndex: "pattern",
          id: "pattern",
          editor: new Ext.form.TextField(),
        },
      ],
      autoExpandColumn: "pattern",
      clicksToEdit: 2,
      height: 200,
      viewConfig: {
        forceFit: false,
      },
      tbar: [
        {
          text: _("Add Rule"),
          iconCls: "icon-add",
          handler: this.onAddRule,
          scope: this,
        },
        {
          text: _("Remove Rule"),
          iconCls: "icon-remove",
          handler: this.onRemoveRule,
          scope: this,
        },
      ],
    });

    // Set items before calling superclass
    Ext.apply(this, {
      items: [
        {
          xtype: "fieldset",
          border: false,
          title: _("AutoLabel"),
          autoHeight: true,
          labelWidth: 1,
          defaultType: "panel",
          items: [
            {
              border: false,
              bodyCfg: {
                html: "<p>Rules will be evaluated when torrents are added.</p><br>",
              },
            },
            this.rulesGrid,
            {
              xtype: "fieldset",
              title: _("Options"),
              autoHeight: true,
              items: [this.caseInsensitiveCheckbox],
            },
          ],
        },
      ],
    });

    Deluge.ux.preferences.AutoLabelPage.superclass.initComponent.call(this);

    this.on("show", this.onPreferencesShow, this);

    // Register the onApply method to be called when preferences are applied or OK is clicked
    deluge.preferences.on("apply", this.onApply, this);
  },

  onPreferencesShow: function () {
    this.loadConfig();
    // Force layout update when showing the panel
    if (this.doLayout) {
      this.doLayout();
    }
  },

  loadConfig: function () {
    var self = this;
    deluge.client.autolabel.get_config({
      success: function (config) {
        if (self.rulesStore) {
          self.rulesStore.loadData(config.rules || []);
        }
        if (self.caseInsensitiveCheckbox) {
          self.caseInsensitiveCheckbox.setValue(config.case_insensitive);
        }
      },
      failure: function () {
        // Ignore failures - config might not exist yet
      },
    });
  },

  onApply: function () {
    this._saveConfig();
  },

  onOk: function () {
    this._saveConfig();
  },

  _saveConfig: function () {
    var rules = [];
    this.rulesStore.each(function (record) {
      rules.push({
        label: record.get("label"),
        pattern: record.get("pattern"),
      });
    });

    var config = {
      rules: rules,
      case_insensitive: this.caseInsensitiveCheckbox.getValue(),
    };

    deluge.client.autolabel.set_config(config);
  },

  onAddRule: function () {
    var Rule = this.rulesStore.recordType;
    var r = new Rule({ label: "new-label", pattern: ".*" });
    this.rulesStore.add(r);
    this.rulesGrid.startEditing(this.rulesStore.getCount() - 1, 0);
  },

  onRemoveRule: function () {
    var sm = this.rulesGrid.getSelectionModel();
    var cell = sm.getSelectedCell();
    if (cell) {
      var record = this.rulesStore.getAt(cell[0]);
      if (record) {
        this.rulesStore.remove(record);
      }
    }
  },
});

Deluge.plugins.AutoLabelPlugin = Ext.extend(Deluge.Plugin, {
  name: "AutoLabel",

  onDisable: function () {
    deluge.preferences.removePage(this.prefsPage);
  },

  onEnable: function () {
    this.prefsPage = deluge.preferences.addPage(
      new Deluge.ux.preferences.AutoLabelPage()
    );
  },
});

Deluge.registerPlugin("AutoLabel", Deluge.plugins.AutoLabelPlugin);
