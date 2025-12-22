/** @odoo-module **/

import { RokAppsWidget } from "@rok_apps/rok_apps_widget";
import { registerRokAppsWidget } from "@rok_apps/rok_apps_widget_registry";

export class WeatherRokAppsWidget extends RokAppsWidget {
    static template = "weather.RokAppsWidget";
    static props = ["record"];
}

// Register the widget for the "Weather" app
registerRokAppsWidget("Weather", WeatherRokAppsWidget);
