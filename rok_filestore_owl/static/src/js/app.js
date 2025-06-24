/** @odoo-module */

import { FilestoreApp } from "./components/FilestoreApp";
import { registry } from "@web/core/registry";

registry.category("actions").add("rok_filestore_owl.filestore_app", FilestoreApp);
