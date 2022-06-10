function autocomplete() {
    const genericExamples = document.querySelectorAll('[data-autocomplete]');

    for (i = 0; i < genericExamples.length; ++i) {
        const element = genericExamples[i];
        // eslint-disable-next-line no-new
        new Choices(element, {
            allowHTML: true,
            searchFields: ['value'],
            placeholderValue: 'Add an item',
            searchPlaceholderValue: 'This is a search placeholder',
            removeItemButton: true,
        });
    }
}

if (document.body.contains(document.querySelector('[data-autocomplete]'))) {
    autocomplete();
}
