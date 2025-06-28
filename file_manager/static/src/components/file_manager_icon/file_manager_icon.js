/** @odoo-module */

import { useEmojiPicker } from "@web/core/emoji_picker/emoji_picker";
import { registry } from "@web/core/registry";
import { exprToBoolean } from "@web/core/utils/strings";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

import { getRandomIcon } from "@file_manager/js/file_manager_utils";

import { Component, useRef } from "@odoo/owl";

export default class FileManagerIcon extends Component {
    static template = "file_manager.FileManagerIcon";
    static props = {
        record: Object,
        readonly: Boolean,
        iconClasses: {type: String, optional: true},
        allowRandomIconSelection: {type: Boolean, optional: true},
        autoSave: {type: Boolean, optional: true},
        fallbackDefaultIcon: { type: Boolean, optional: true },
    };

    setup() {
        super.setup();
        this.iconRef = useRef("icon");
        this.emojiPicker = useEmojiPicker(this.iconRef, { hasRemoveFeature: true, onSelect: this.updateIcon.bind(this) });
    }

    get icon() {
        return this.props.record.data.icon || (this.props.fallbackDefaultIcon && "📄");
    }

    async selectRandomIcon() {
        this.updateIcon(await getRandomIcon());
    }

    updateIcon(icon) {
        this.props.record.update({icon});
        if (this.props.autoSave) {
            this.props.record.save();
        }
    }
}

class FileManagerIconField extends FileManagerIcon {
    static props = {
        ...standardFieldProps,
        allowRandomIconSelection: Boolean,
        autoSave: Boolean,
    };
}

registry.category("fields").add("file_manager_icon", {
    component: FileManagerIconField,
    extractProps({ attrs, viewType }, dynamicInfo) {
        return {
            autoSave: viewType === "kanban",
            readonly: dynamicInfo.readonly,
            allowRandomIconSelection: exprToBoolean(attrs.allow_random_icon_selection),
        };
    },
});
