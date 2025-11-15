/** @odoo-module **/

import { registry } from "@web/core/registry";
import { GraphRenderer } from "@web/views/graph/graph_renderer";
import { graphView } from "@web/views/graph/graph_view";
import { Weather } from "../../components/weather";

const viewRegistry = registry.category("views");

export class WeatherGraphRenderer extends GraphRenderer {
    static template = "weather.WeatherGraphRenderer";
    static components = { ...GraphRenderer.components, Weather };
};

export const WeatherGraphView = {
    ...graphView,
    Renderer: WeatherGraphRenderer,
};

viewRegistry.add("weather_graph", WeatherGraphView);
