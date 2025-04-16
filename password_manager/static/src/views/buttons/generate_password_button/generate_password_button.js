import { _t } from "@web/core/l10n/translation";
import { PasswordGeneratorDialog } from "../../dialogs/password_generator_dialog";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";

export class GeneratePasswordButton extends Component {
    static template = "passwords.GeneratePasswordButton";
    static props = {
        className: { type: String, optional: true },
        disabled: { type: Boolean, optional: true },
        icon: { type: String, optional: true },
        value: { type: String, optional: true },
        useGeneratedValue: { type: Function },
    };

    setup() {
        super.setup();
        this.dialog = useService("dialog");
        this.useGeneratedValue = this._useGeneratedValue.bind(this);
        this.successText = _t("Copied");
    }

    async onClick() {
        this.dialog.add(PasswordGeneratorDialog, {
            title: 'Generator',
            value: this.props.value,
            isPassphrase: false,
            len: 10,
            useCapitalLetters: true,
            useLowercaseLetters: true,
            useDigits: true,
            useSpecials: true,
            minimumNumbers: 3,
            minimumSpecials: 3,
            avoidAmbiguous: true,
            wordSeparator: "-",
            useGeneratedValue: this.props.useGeneratedValue,
        });
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
        this.props.useGeneratedValue(
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
        );
        console.log("value: " + value);
    }


}
