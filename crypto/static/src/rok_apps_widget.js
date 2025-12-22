/** @odoo-module **/

import { RokAppsWidget } from "@rok_apps/rok_apps_widget";
import { registerRokAppsWidget } from "@rok_apps/rok_apps_widget_registry";

export class CryptoRokAppsWidget extends RokAppsWidget {
    static template = "crypto.RokAppsWidget";
    static props = ["record"];
}

// Register the widget for the "Crypto" app
registerRokAppsWidget("Crypto", CryptoRokAppsWidget);
