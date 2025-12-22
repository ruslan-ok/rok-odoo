/** @odoo-module **/

import { Component } from "@odoo/owl";
import { getRokAppsWidget } from "./rok_apps_widget_registry";

export class RokAppsWidget extends Component {
    static template = "rok_apps.RokAppsWidget";
    static props = ["record"];

    get recordName() {
        return this.props.record?.data?.name || "No name";
    }

    get widgetComponent() {
        const appName = this.recordName;
        return getRokAppsWidget(appName) || null;
    }
}
