import { Component, useState } from "@odoo/owl";
import { CheckBox } from "@web/core/checkbox/checkbox";
import {debounce} from "@web/core/utils/timing";


export class CheckboxGroup extends Component {
    static template = "password_manager.CheckboxGroup";
    static components = { CheckBox };
    static props = {
        values: { type: Array },
        update: { type: Function },
    };

    setup() {
        super.setup();
        this.checkboxes = useState(this.props.values);
        this.debouncedCommitChanges = debounce(this.commitChanges.bind(this), 100);
    }

    commitChanges() {
        this.props.update(this.checkboxes);
    }

    onChange(key, checked) {
        this.checkboxes[key]['checked'] = checked;
        this.debouncedCommitChanges();
    }

}
