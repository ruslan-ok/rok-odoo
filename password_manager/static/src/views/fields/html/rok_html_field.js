import { registry } from "@web/core/registry";
import { TextField, textField } from "@web/views/fields/text/text_field";
import { markup } from "@odoo/owl";

export class RokHtmlField extends TextField {
    static template = "web.RokHtmlField";

    cuttedContent(content) {
        const parser = new DOMParser();
        const htmlDoc = parser.parseFromString(content, 'text/html');
        this.walk(htmlDoc.body, 100);
        const newContent = markup(htmlDoc.body.innerHTML);
        return newContent;
    }

    walk(node, maxLen) {
        let child, next;
        let newMaxLen = maxLen;
        switch (node.nodeType) {
            case Node.TEXT_NODE:
                newMaxLen = this.handleText(node, maxLen);
                break;
            case Node.ELEMENT_NODE:
                if (node.tagName === "P" || node.tagName === "BR") {
                    var d = document.createElement('span');
                    d.innerHTML = node.innerHTML;
                    if (node.tagName) {
                        d.classList.add("ms-2");
                    }
                    node.parentNode.replaceChild(d, node);
                    node = d;
                }

                child = node.firstChild;

                if (!child) {
                    newMaxLen = this.handleText(node, maxLen);
                }

                while (child) {
                    next = child.nextSibling;
                    newMaxLen = this.walk(child, newMaxLen);
                    child = next;
                }
                break;
        }
        return newMaxLen;
    }

    handleText(node, maxLen) {
        let v = maxLen > 0 ? node.textContent : "";
        if (maxLen > 0 && v.length > maxLen) {
            v = v.substring(0, maxLen) + "...";
        }
        node.textContent = v;
        return maxLen - v.length;
    }
}

export const rokHtmlField = {
    ...textField,
    component: RokHtmlField,
};

registry.category("fields").add("rok_html", rokHtmlField);
