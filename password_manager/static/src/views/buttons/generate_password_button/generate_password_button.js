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
    }

    async onClick() {
        this.dialog.add(PasswordGeneratorDialog, {
            title: "Generator",
            value: this.props.value,
            useGeneratedValue: this.props.useGeneratedValue,
        });
    }
}
