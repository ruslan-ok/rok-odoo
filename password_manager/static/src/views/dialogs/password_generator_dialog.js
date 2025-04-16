import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { CopyButton } from "@web/core/copy_button/copy_button";
import { CheckboxGroup } from "../fields/checkbox_group/checkbox_group";

import { Component, useState, useRef } from "@odoo/owl";

class RadioSelection extends Component {
    static template = "password_manager.RadioSelection";
    static props = {
        choices: Array,
        onChange: Function,
        selectedValue: { optional: false },
        name: String,
    };
    static defaultProps = {};
}

const PASSPHRASE_CHOICES = [
    { value: "0", label: _t("Password") },
    { value: "1", label: _t("Passphrase") },
];

export class PasswordGeneratorDialog extends Component {
    static template = "password_manager.PasswordGeneratorDialog";
    static components = { Dialog, CopyButton, RadioSelection, CheckboxGroup };
    static props = {
        value: { type: String },
        isPassphrase: { type: Boolean, optional: true },
        len: { type: Number, optional: true },
        includeUppercase: { type: Boolean, optional: true },
        includeLowercase: { type: Boolean, optional: true },
        includeNumbers: { type: Boolean, optional: true },
        includeSpecial: { type: Boolean, optional: true },
        avoidAmbiguous: { type: Boolean, optional: true },
        minimumNumbers: { type: Number, optional: true },
        minimumSpecials: { type: Number, optional: true },
        wordSeparator: { type: String, optional: true },
        useGeneratedValue: { type: Function },
    };

    setup() {
        this.state = useState({
            value: this.props.value,
            isPassphrase: this.props.isPassphrase,
            len: this.props.len,
            minimumNumbers: this.props.minimumNumbers,
            minimumSpecials: this.props.minimumSpecials,
            wordSeparator: this.props.wordSeparator,
        });
        this.passphraseChoices = PASSPHRASE_CHOICES;
        this.includeValues = [
            {
                id: 0,
                label: "A-Z",
                checked: true,
                disabled: true,
                question_circle: "Include uppercase charackters",
            },
            {
                id: 1,
                label: "a-z",
                checked: this.props.includeLowercase,
                disabled: false,
                question_circle: "Include lowercase charackters",
            },
            {
                id: 2,
                label: "0-9",
                checked: this.props.includeNumbers,
                disabled: false,
                question_circle: "Include numbers",
            },
            {
                id: 3,
                label: "!@#$%^&*",
                checked: this.props.includeSpecial,
                disabled: false,
                question_circle: "Include special charackters",
            },
            {
                id: 4,
                label: "Avoid ambiguous characters",
                checked: this.props.avoidAmbiguous,
                disabled: false,
                question_circle: false,
            },
        ];
        this.env.dialogData.dismiss = () => this.discardRecord();
        this.useGeneratedValue = this.useThisPassword.bind(this);
        this.updateStateValue = this._updateStateValue.bind(this);
        this.updatePassphrase = this._updatePassphrase.bind(this);
        this.successText = _t("Copied");
        this.value_input = useRef("value_input");
        this.passphrase_input = useRef("passphrase_input");
    }

    useThisPassword() {
        this.props.useGeneratedValue(
            this.state.value,
            this.passphrase_input.el.value,
            this.state.len,
            this.state.useCapitalLetters,
            this.state.useLowercaseLetters,
            this.state.useDigits,
            this.state.useSpecials,
            this.state.minimumNumbers,
            this.state.minimumSpecials,
            this.state.avoidAmbiguous,
            this.state.wordSeparator,
        );
        this.props.close();
    }

    discardRecord() {
        this.props.close();
    }

    onRegenerateClick() {
        console.log("onRegenerateClick");
    }

    _updateStateValue() {
        this.state.value = this.value_input.el.value;
    }

    _updatePassphrase(val) {
        this.state.isPassphrase = val === "1";
    }
}
