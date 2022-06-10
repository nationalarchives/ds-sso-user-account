class ConditionalField {
    static selector() {
        return '[data-conditional-field]';
    }

    constructor(node) {
        this.node = node;
        this.hiddenContent = this.bindEvents(node);
    }

    checkActive(el) {
        const hiddenPanels = document.querySelectorAll('.conditional-field');

        hiddenPanels.forEach((element) => {
            element.classList.add('d-none');
        });

        if (this.node.querySelector('input').checked) {
            el.querySelector('.conditional-field').classList.remove('d-none');
        }
    }

    bindEvents(el) {
        el.addEventListener('change', () => {
            this.checkActive(el);
        });
    }
}

export default ConditionalField;
