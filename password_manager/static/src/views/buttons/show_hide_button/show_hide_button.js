import { Component } from "@odoo/owl";

export class ShowHideButton extends Component {
    static template = "passwords.ShowHideButton";
    static props = {
        className: { type: String, optional: true },
        showHideText: { type: String, optional: true },
        disabled: { type: Boolean, optional: true },
        icon: { type: String, optional: true },
        content: { type: [String, Object], optional: true },
        toggleSensitive: { type: Function, optional: true },
    };

    async onClick() {
        this.props.toggleSensitive();
    }
}
