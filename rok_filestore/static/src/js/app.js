/** @odoo-module */

import { FilestoreApp } from "./components/FilestoreApp";
import { registry } from "@web/core/registry";

registry.category("actions").add("rok_filestore.filestore_app", FilestoreApp);
