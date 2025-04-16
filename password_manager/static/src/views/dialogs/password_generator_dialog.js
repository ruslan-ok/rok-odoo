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
        const isPassphrase = this.getStorageItem("is_passphrase") === "1";
        this.passwordLength = this.getStorageItem("password_length") || 15;
        this.numberOfWords = this.getStorageItem("number_of_words") || 6;
        this.state = useState({
            value: this.props.value,
            isPassphrase: isPassphrase,
            passwordLength: isPassphrase ? this.numberOfWords : this.passwordLength,
            minimumNumbers: this.getStorageItem("minimum_numbers") || 1,
            minimumSpecials: this.getStorageItem("minimum_specials") || 1,
            wordSeparator: this.getStorageItem("word_separator") || "-",
            capitalize: this.getStorageItem("capitalize") === "1",
            includeNumber: this.getStorageItem("include_number") === "1",
        });
        this.passphraseChoices = PASSPHRASE_CHOICES;
        this.env.dialogData.dismiss = () => this.discardRecord();
        let includeValues = [];
        INCLUDE_VALUES.forEach((vals) => {
            let newVals = vals;
            if (vals.name === "uppercase")
                newVals.checked = true;
            else
                newVals.checked = this.getStorageItem("include_" + vals.name) === "1";
            includeValues.push(newVals);
        });
        this.includeValues = includeValues;
        this.debugValue = 100;
        this.generateNewValue();
    }

    discardRecord() {
        this.props.close();
    }

    generateNewValue() {
        this.debugValue++;
        this.state.value = this.debugValue.toString();
        console.log("generateNewValue: " + this.state.value);
    }

    updateValue() {
        this.state.value = this.value_input.el.value;
    }

    getStorageItem(name) {
        return localStorage.getItem(name);
    }

    setStorageItem(name, value) {
        localStorage.setItem(name, value);
    }

    togglePasswordPassphrase(value) {
        console.log("togglePasswordPassphrase: " + value);
        this.setStorageItem("is_passphrase", value);
        this.state.isPassphrase = value === "1";
        this.state.passwordLength = this.state.isPassphrase ? this.numberOfWords : this.passwordLength;
        this.generateNewValue();
    }

    updateInclude(data) {
        data.forEach(item => this.setStorageItem("include_" + item.name, item.checked ? "1" : "0"));
        this.generateNewValue();
    }

    get passwordLengthLabel() {
        if (this.state.isPassphrase)
            return _t("Number of words");
        return _t("Length");
    }

    get passwordLengthClarification() {
        if (this.state.isPassphrase)
            return _t("Value must be between 3 and 20. Use 6 words or more to generate a strong passphrase.");
        return _t("Value must be between 10 and 128. Use 14 characters or more to generate a strong password.");
    }

    get minLength() {
        if (this.state.isPassphrase)
            return "3";
        return "10";
    }

    get maxLength() {
        if (this.state.isPassphrase)
            return "20";
        return "128";
    }

    get isMinimumNumbersDisabled() {
        return !this.includeValues.filter(x => x.name === "numbers")[0].checked;
    }

    get isMinimumSpecialsDisabled() {
        return !this.includeValues.filter(x => x.name === "special")[0].checked;
    }

    lengthChanged(el) {
        console.log("lengthChanged: " + el.target.value);
        if (this.state.isPassphrase) {
            this.numberOfWords = el.target.value;
            this.setStorageItem("number_of_words", this.numberOfWords);
            this.state.passwordLength = this.numberOfWords;
        } else {
            this.passwordLength = el.target.value;
            this.setStorageItem("password_length", this.passwordLength);
            this.state.passwordLength = this.passwordLength;
        }
        this.generateNewValue();
    }

    wordSeparatorChanged(el) {
        console.log("wordSeparatorChanged: " + el.target.value);
        this.state.wordSeparator = el.target.value;
        this.setStorageItem("word_separator", this.state.wordSeparator);
        this.generateNewValue();
    }

    capitalizeChanged(el) {
        console.log("capitalizeChanged: " + el.target.checked);
    }

    includeNumberChanged(el) {
        console.log("includeNumberChanged: " + el.target.checked);
    }

    useThisValue() {
        this.props.useGeneratedValue(
            this.state.value,
        );
        this.props.close();
    }

    showHistory() {
        console.log("showHistory");
    }
}
