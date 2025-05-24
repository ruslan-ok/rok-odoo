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
        direction: { type: String, optional: true, default: "horizontal" },
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
        name: "upper",
        disabled: true,
        question_circle: "Include uppercase charackters",
    },
    {
        id: 1,
        label: "a-z",
        name: "lower",
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
        name: "avoid",
        disabled: false,
        question_circle: false,
    },
];

class PasswordGenerator {
    constructor(state, use) {
        this.debugValue = 100;
        this.isPassphrase = state.isPassphrase;
        this.passwordLength = state.passwordLength;
        this.minimumNumbers = state.minimumNumbers;
        this.minimumSpecials = state.minimumSpecials;
        this.use = use;
        this.alphabet = {
            upper: "ABCDEFGHJKLMNPQRSTUVWXYZ" + (this.use.avoid ? "" : "IO"),
            lower: "abcdefghjklmnpqrstuvwxyz" + (this.use.avoid ? "" : "io"),
            numbers: "23456789" + (this.use.avoid ? "" : "01"),
            special: "!@#$%^&*",
        };
        this.value = "";
    }

    getPasswordChar(part, data) {
        if (!this.workLength)
            return "";
        let str = data;
        switch (part) {
            case "upper": str = this.alphabet.upper; break;
            case "lower": str = this.alphabet.lower; break;
            case "numbers": str = this.alphabet.numbers; break;
            case "special": str = this.alphabet.special; break;
        }
        const idx = Math.floor(Math.random() * str.length);
        this.workLength--;
        return str.charAt(idx);
    }

    shuffle() {
        let str = this.value;
        let result = "";
        while (str.length) {
            const idx = Math.floor(Math.random() * str.length);
            result += str.charAt(idx);
            str = str.slice(0, idx) + str.slice(idx + 1);
        }
        this.value = result;
    }

    generate() {
        this.workLength = this.passwordLength;
        this.value = "";
        if (this.isPassphrase) {
            this.debugValue++;
            this.value = this.debugValue.toString();
        } else {
            let data = this.alphabet.upper;
            this.value = this.getPasswordChar("upper", "");
            if (this.use.numbers) {
                data += this.alphabet.numbers;
                for (let i = 0; i < this.minimumNumbers; i++) {
                    this.value += this.getPasswordChar("numbers", "");
                }
            }
            if (this.use.special) {
                data += this.alphabet.special;
                for (let i = 0; i < this.minimumSpecials; i++) {
                    this.value += this.getPasswordChar("special", "");
                }
            }
            if (this.use.lower) {
                data += this.alphabet.lower;
                this.value += this.getPasswordChar("lower", "");
            }
            while (this.workLength)
                this.value += this.getPasswordChar("", data);
            this.shuffle();
        }
        return this.value;
    }
}

class Point {
    constructor(x, y) {
      this.x = x;
      this.y = y;
    }
  
    static displayName = "Point";
    static distance(a, b) {
      const dx = a.x - b.x;
      const dy = a.y - b.y;
  
      return Math.hypot(dx, dy);
    }
}
  
  
export class PasswordGeneratorDialog extends Component {
    static template = "password_manager.PasswordGeneratorDialog";
    static components = { Dialog, CopyButton, RadioSelection, CheckboxGroup };
    static props = {
        value: { type: String },
        useGeneratedValue: { type: Function },
        title: { type: String },
        close: { type: Function },
    };

    setup() {
        this.successText = _t("Copied");
        this.value_input = useRef("value_input");
        const isPassphrase = this.getStorageItem("is_passphrase") === "1";
        this.passwordLength = +this.getStorageItem("password_length") || 15;
        this.numberOfWords = +this.getStorageItem("number_of_words") || 6;
        this.state = useState({
            value: this.props.value,
            isPassphrase: isPassphrase,
            passwordLength: isPassphrase ? this.numberOfWords : this.passwordLength,
            minimumNumbers: +this.getStorageItem("minimum_numbers") || 1,
            minimumSpecials: +this.getStorageItem("minimum_specials") || 1,
            wordSeparator: this.getStorageItem("word_separator") || "-",
            capitalize: this.getStorageItem("capitalize") === "1",
            includeNumber: this.getStorageItem("include_number") === "1",
        });
        this.passphraseChoices = PASSPHRASE_CHOICES;
        this.env.dialogData.dismiss = () => this.discardRecord();
        this.initUse();
        this.debugValue = 100;
        this.generateNewValue();
    }

    discardRecord() {
        this.props.close();
    }

    initUse() {
        if (this.state.isPassphrase)
            return;
        let includeValues = [];
        INCLUDE_VALUES.forEach((vals) => {
            let newVals = vals;
            if (vals.name === "upper")
                newVals.checked = true;
            else
                newVals.checked = this.getStorageItem("include_" + vals.name) === "1";
            includeValues.push(newVals);
        });
        this.includeValues = includeValues;
        this.use = includeValues.reduce((result, x) => {result[x.name] = x.checked; return result;}, {});
        let minLen = 2;
        if (this.use.lower)
            minLen++;
        if (this.use.numbers)
            minLen += this.state.minimumNumbers;
        if (this.use.special)
            minLen += this.state.minimumSpecials;
        if (this.state.passwordLength < minLen)
            this.state.passwordLength = minLen;
    }

    generateNewValue() {
        const generator = new PasswordGenerator(this.state, this.use);
        this.state.value = generator.generate();
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
        this.initUse();
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
        return !this.use.numbers;
    }

    get isMinimumSpecialsDisabled() {
        return !this.use.special;
    }

    lengthChanged(el) {
        console.log("lengthChanged: " + el.target.value);
        if (this.state.isPassphrase) {
            this.numberOfWords = +el.target.value;
            this.setStorageItem("number_of_words", this.numberOfWords);
            this.state.passwordLength = this.numberOfWords;
        } else {
            this.passwordLength = +el.target.value;
            this.setStorageItem("password_length", this.passwordLength);
            this.state.passwordLength = this.passwordLength;
        }
        this.generateNewValue();
    }

    minNumbersChanged(el) {
        this.state.minimumNumbers = +el.target.value;
        if (this.state.minimumNumbers < 1)
            this.state.minimumNumbers = 1;
        if (this.state.minimumNumbers > 9)
            this.state.minimumNumbers = 9;
        let mandatory = this.state.minimumSpecials + (this.use.special ? this.state.minimumSpecials : 0) + 2;
        if (this.state.passwordLength < mandatory)
            this.state.passwordLength = mandatory;
        this.setStorageItem("minimum_numbers", this.state.minimumNumbers);
        this.generateNewValue();
    }

    minSpecialsChanged(el) {
        this.state.minimumSpecials = +el.target.value;
        if (this.state.minimumSpecials < 1)
            this.state.minimumSpecials = 1;
        if (this.state.minimumSpecials > 9)
            this.state.minimumSpecials = 9;
        let mandatory = this.state.minimumSpecials + (this.use.numbers ? this.state.minimumNumbers : 0) + 2;
        if (this.state.passwordLength < mandatory)
            this.state.passwordLength = mandatory;
        this.setStorageItem("minimum_specials", this.state.minimumSpecials);
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
