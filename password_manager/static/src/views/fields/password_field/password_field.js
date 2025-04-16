import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { useInputField } from "@web/views/fields/input_field_hook";
import { CharField } from "@web/views/fields/char/char_field";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { CopyButton } from "@web/core/copy_button/copy_button";
import { ShowHideButton } from "../../buttons/show_hide_button/show_hide_button";
import { GeneratePasswordButton } from "../../buttons/generate_password_button/generate_password_button";

import { useState, useRef, Component } from "@odoo/owl";

export class PasswordField extends Component {
    static template = "password_manager.ListPasswordField";
    static components = { Field: CharField, CopyButton };
    static props = {
        ...standardFieldProps,
        placeholder: { type: String, optional: true },
    };

    setup() {
        useInputField({ getValue: () => this.props.record.data[this.props.name] || "" });
        this.successText = _t("Copied");
        this.sensitiveHiddenValue = "**********";
        this.sensitiveValue = this.props.name === "value";
        this.state = useState({ hideSensitive: true });
        this.input = useRef("input");
        this.useGeneratedValue = this._useGeneratedValue.bind(this);
    }

    toggleSensitive() {
        this.state.hideSensitive = !this.state.hideSensitive;
        this.input.type = "text";
    }

    get inputType() {
        if (this.sensitiveValue && this.state.hideSensitive)
            return "password";
        return "text";
    }

    get listFieldValue() {
        if (this.sensitiveValue && this.state.hideSensitive)
            return this.sensitiveHiddenValue;
        return this.props.record.data[this.props.name];
    }

    get inputType() {
        if (this.sensitiveValue && this.state.hideSensitive)
            return "password";
        return "text";
    }

    get copyButtonIcon() {
        return "fa-clone";
    }

    get copyButtonClassName() {
        return `o_btn_copy btn-sm`;
    }

    get showHideButtonIcon() {
        if (this.state.hideSensitive)
            return "fa-eye-slash";
        return "fa-eye";
    }

    get showHideButtonClassName() {
        return `o_btn_show_hide btn-sm`;
    }

    get generatePasswordButtonIcon() {
        return "fa-rotate-right";
    }

    _useGeneratedValue(
        value,
        isPassphrase, 
        len, 
        useCapitalLetters, 
        useLowercaseLetters, 
        useDigits, 
        useSpecials, 
        minimumNumbers, 
        minimumSpecials, 
        avoidAmbiguous, 
        wordSeparator
    ) {
        this.props.record.data[this.props.name] = value;
        console.log(this.props.record.data[this.props.name]);
    }
}

export const passwordField = {
    component: PasswordField,
    displayName: _t("Password"),
};

registry.category("fields").add("list_password", passwordField);

class FormPasswordField extends PasswordField {
    static components = { CopyButton, ShowHideButton, GeneratePasswordButton };
    static template = "password_manager.FormPasswordField";
}

export const formPasswordField = {
    ...passwordField,
    component: FormPasswordField,
};

registry.category("fields").add("form_password", formPasswordField);
