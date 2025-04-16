// import { _t } from "@web/core/l10n/translation";
import { PasswordGeneratorDialog } from "../../dialogs/password_generator_dialog";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";

export class GeneratePasswordButton extends Component {
    static template = "password_manager.GeneratePasswordButton";
    static props = {
        value: { type: String, optional: true },
        useGeneratedValue: { type: Function },
    };

    setup() {
        super.setup();
        this.dialog = useService("dialog");
        // this.useGeneratedValue = this._useGeneratedValue.bind(this);
    }

    async onClick() {
        this.dialog.add(PasswordGeneratorDialog, {
            value: this.props.value,
            useGeneratedValue: this.props.useGeneratedValue,
        });
    }

    // useGeneratedValue(
    //     value,
    //     isPassphrase, 
    //     len, 
    //     useCapitalLetters, 
    //     useLowercaseLetters, 
    //     useDigits, 
    //     useSpecials, 
    //     minimumNumbers, 
    //     minimumSpecials, 
    //     avoidAmbiguous, 
    //     wordSeparator
    // ) {
    //     this.props.useGeneratedValue(
    //         value,
    //         isPassphrase, 
    //         len, 
    //         useCapitalLetters, 
    //         useLowercaseLetters, 
    //         useDigits, 
    //         useSpecials, 
    //         minimumNumbers, 
    //         minimumSpecials, 
    //         avoidAmbiguous, 
    //         wordSeparator
    //     );
    //     console.log("value: " + value);
    // }


}
