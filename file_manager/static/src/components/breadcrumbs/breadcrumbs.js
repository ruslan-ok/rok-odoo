import { useService } from "@web/core/utils/hooks";
import { useRecordObserver } from "@web/model/relational_model/utils";

import { Component } from "@odoo/owl";

export default class FileManagerBreadcrumbs extends Component {
    static template = "file_manager.FileManagerBreadcrumbs";
    static props = {
        record: Object,
    };

    setup() {
        super.setup();
        this.actionService = useService("action");
        this.fileIndexes = [this.props.record.resId];
        this.fileIndexe = 0;
        this.canRestorePreviousAction = this.env.config.breadcrumbs?.length > 1;
        useRecordObserver((record) => {
            // When a folder is opened, update the array of ids if it was not opened using the
            // breadcrumbs. For example, if the array of ids is [1,2,3,4] and we are currently on
            // the folder 2 after having clicked twice on the back button, opening folder 5
            // discards the ids after 2 and appends id 5 to the array ([1,2,5])
            if (record.resId !== this.fileIndexes[this.fileIndexe]) {
                this.fileIndexes.splice(
                    ++this.fileIndexe,
                    this.fileIndexes.length - this.fileIndexe,
                    record.resId,
                );
            }
        });
    }

    get isGoBackEnabled() {
        return this.fileIndexe > 0 || this.canRestorePreviousAction;
    }

    get isGoNextEnabled() {
        return this.fileIndexe < this.fileIndexes.length - 1;
    }

    onClickBack() {
        if (this.isGoBackEnabled) {
            if (this.fileIndexe === 0) {
                this.actionService.restore();
            } else {
                this.env.openFolder(this.fileIndexes[--this.fileIndexe]);
            }
        }
    }

    onClickNext() {
        if (this.isGoNextEnabled) {
            this.env.openFolder(this.fileIndexes[++this.fileIndexe]);
        }
    }
}
