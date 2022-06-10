class BulkEdit {
    static selector() {
        return '[data-bulk-update]';
    }

    constructor(node) {
        this.node = node;
        this.checkboxes = document.querySelectorAll('[data-bulk-update]');
        this.selectMenu = document.querySelectorAll('[data-bulk-action]');
        this.selectOptions = document
            .querySelector('[data-bulk-action]')
            .querySelector('option');
        this.bindEvents(node);
        this.defaultSelectText = 'Bulk update';
    }

    atLeastOneCheckboxIsChecked() {
        const checkboxes = Array.from(this.checkboxes);
        return checkboxes.reduce((acc, curr) => acc || curr.checked, false);
    }

    checkActive() {
        if (this.atLeastOneCheckboxIsChecked() === true) {
            this.displayBulkEdit();
        } else {
            this.hideBulkEdit();
        }
    }

    displayBulkEdit() {
        this.selectMenu.forEach((el) => {
            el.disabled = false;
            this.addCount();
        });
    }

    hideBulkEdit() {
        this.selectMenu.forEach((el) => {
            el.disabled = true;
            this.removeCount();
        });
    }

    addCount() {
        this.selectMenu.forEach((el) => {
            el.querySelector('option').text = 'Bulk update (5)';
        });
    }

    removeCount() {
        this.selectMenu.forEach((el) => {
            el.querySelector('option').text = this.defaultSelectText;
        });
    }

    bindEvents(node) {
        node.addEventListener('change', () => {
            this.atLeastOneCheckboxIsChecked();
            this.checkActive();
        });
    }
}

export default BulkEdit;
