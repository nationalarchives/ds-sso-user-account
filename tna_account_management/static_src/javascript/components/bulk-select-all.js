class BulkSelectAll {
    static selector() {
        return '[data-bulk-select-all]';
    }

    constructor(node) {
        this.node = node;
        this.bulkItems = document.querySelectorAll('[data-bulk-update]');

        this.bindEvents(node);
    }

    checkActive() {
        const isChecked = this.node.checked;

        if (isChecked) {
            this.selectAll();
        } else {
            this.deSelectAll();
        }
    }

    selectAll() {
        this.bulkItems.forEach((el) => {
            el.checked = true;
        });
    }

    deSelectAll() {
        this.bulkItems.forEach((el) => {
            el.checked = false;
        });
    }

    bindEvents(node) {
        node.addEventListener('change', (e) => {
            this.checkActive(e);
        });
    }
}

export default BulkSelectAll;
