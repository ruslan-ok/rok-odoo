import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";

function getActiveCategoryId(env, fieldName) {
    const categories = env.searchModel?.categories || [];
    for (const category of categories) {
        if (category.fieldName === fieldName) {
            return category.activeValueId || false;
        }
    }
    return false;
}

patch(ListController.prototype, {
    async createRecord(options = {}) {
        try {
            const resModel = this.model?.root?.resModel;
            if (resModel === "passwords") {
                const categId = getActiveCategoryId(this.env, "categ_id");
                if (categId) {
                    await this.actionService.doAction(
                        {
                            type: "ir.actions.act_window",
                            res_model: "passwords",
                            views: [[false, "form"]],
                            target: "current",
                            context: { default_categ_id: categId },
                        },
                        {
                            // When the form closes, reload the list to reflect potential changes
                            onClose: async () => {
                                if (this.model?.root?.load) {
                                    await this.model.root.load();
                                }
                            },
                        }
                    );
                    return;
                }
            }
        } catch (e) {
            // Fallback to default behavior on any error
        }
        return await this._super(options);
    },
});


