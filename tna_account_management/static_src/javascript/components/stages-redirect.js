class StagesRedirect {
    static selector() {
        return '#sort-stage';
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

export default StagesRedirect;
