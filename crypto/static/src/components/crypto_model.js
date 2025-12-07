/** @odoo-module **/

import { Model } from "@web/model/model";


export class CryptoModel extends Model {
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
        this.searchParams = searchParams;
        await this._fetchDataPoints(this.metaData);
    }
}