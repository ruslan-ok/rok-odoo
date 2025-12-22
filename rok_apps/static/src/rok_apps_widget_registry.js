/** @odoo-module **/

/**
 * Registry for RokApps widget components.
 * Each module can register its own widget implementation for a specific app name.
 */
export const rokAppsWidgetRegistry = {};

/**
 * Register a widget component for a specific app name.
 * @param {string} appName - The name of the app (e.g., "Crypto", "Weather")
 * @param {Component} componentClass - The component class to use for this app
 */
export function registerRokAppsWidget(appName, componentClass) {
    rokAppsWidgetRegistry[appName] = componentClass;
}

/**
 * Get a widget component for a specific app name.
 * @param {string} appName - The name of the app
 * @returns {Component|null} The registered component class or null if not found
 */
export function getRokAppsWidget(appName) {
    return rokAppsWidgetRegistry[appName] || null;
}
