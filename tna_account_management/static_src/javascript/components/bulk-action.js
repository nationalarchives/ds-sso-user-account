class BulkAction {
    static selector() {
        return '#sort-bulk-edit';
    }

    constructor(node) {
        this.node = node;
        this.bindEvents(node);
    }

    bindEvents(node) {
        node.addEventListener('change', () => {
            window.location = this.node.value;
        });
    }
}

export default BulkAction;
