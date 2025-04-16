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

const INCLUDE_VALUES = [
    {
        id: 0,
        label: "A-Z",
        name: "uppercase",
        disabled: true,
        question_circle: "Include uppercase charackters",
    },
    {
        id: 1,
        label: "a-z",
        name: "lowercase",
        disabled: false,
        question_circle: "Include lowercase charackters",
    },
    {
        id: 2,
        label: "0-9",
        name: "numbers",
        disabled: false,
        question_circle: "Include numbers",
    },
    {
        id: 3,
        label: "!@#$%^&*",
        name: "special",
        disabled: false,
        question_circle: "Include special charackters",
    },
    {
        id: 4,
        label: "Avoid ambiguous characters",
        name: "ambiguous",
        disabled: false,
        question_circle: false,
    },
];

export class PasswordGeneratorDialog extends Component {
    static template = "password_manager.PasswordGeneratorDialog";
    static components = { Dialog, CopyButton, RadioSelection, CheckboxGroup };
    static props = {
        value: { type: String },
        useGeneratedValue: { type: Function },
    };

    setup() {
        this.successText = _t("Copied");
        this.value_input = useRef("value_input");
        this.state = useState({value: this.props.value});
        this.passphraseChoices = PASSPHRASE_CHOICES;
        this.env.dialogData.dismiss = () => this.discardRecord();
        this.params = {
            isPassphrase: this.getStorageItem("is_passphrase"),
        };
        let includeValues = [];
        INCLUDE_VALUES.forEach((vals) => {
            let newVals = vals;
            if (vals.name === "uppercase")
                newVals.checked = true;
            else
                newVals.checked = this.getStorageItem(vals.name) === true;
            includeValues.push(newVals);
        });
        this.includeValues = includeValues;
        this.generateNewValue();
    }

    useThisValue() {
        this.props.useGeneratedValue(
            this.state.value,
        );
        this.props.close();
    }

    discardRecord() {
        this.props.close();
    }

    generateNewValue() {
        console.log("generateNewValue");
    }

    updateValue() {
        this.state.value = this.value_input.el.value;
    }

    getStorageItem(name) {
        return localStorage.getItem(name);
    }

    setStorageItem(name, value) {
        localStorage.setItem(name, value);
        this.generateNewValue();
    }
}
