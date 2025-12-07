/** @odoo-module **/

import { GraphModel } from "@web/views/graph/graph_model";


export class CryptoModel extends GraphModel {
    /**
     * @override
     */
    setup(params) {
        super.setup(params);
        this.metaData = params;
        this.data = null;
        this.searchParams = null;
    }

    async load(searchParams) {
        // debugger;
        // this.searchParams = searchParams;
        // await this._fetchDataPoints(this.metaData);
        await super.load(searchParams);
    }
}