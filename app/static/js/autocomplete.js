/**
 * BikerZone Autocomplete Component
 *
 * Replaces <select> elements with a searchable autocomplete input.
 * Supports: static options from <select>, async data loading, keyboard navigation,
 * pre-selection for edit forms, and dynamic cloning (for purchase order line items).
 *
 * Usage:
 *   BZAutocomplete.init('#client_id', { placeholder: 'Buscar cliente...' });
 *   BZAutocomplete.init('#motorcycle_id', { async: '/ordenes/api/motos/{client_id}', dependsOn: 'client_id' });
 */
const BZAutocomplete = (function () {
    'use strict';

    let instances = {};

    /**
     * Initialize autocomplete on a <select> element.
     * @param {string} selector - CSS selector for the <select> element
     * @param {Object} options - Configuration
     * @param {string} options.placeholder - Input placeholder text
     * @param {string} options.async - URL template for AJAX loading (use {id} as placeholder)
     * @param {string} options.dependsOn - ID of another autocomplete/select that triggers reload
     * @param {string} options.emptyText - Text when no options available
     * @param {Function} options.onChange - Callback when selection changes
     */
    function init(selector, options) {
        options = options || {};

        // Accept both CSS selector string and DOM element
        var select;
        if (typeof selector === 'string') {
            select = document.querySelector(selector);
        } else if (selector && selector.tagName === 'SELECT') {
            select = selector;
        }

        if (!select || select.dataset.bzAutocomplete) return;

        // Mark as initialized
        select.dataset.bzAutocomplete = 'true';

        const id = select.id || 'bz-ac-' + Math.random().toString(36).slice(2, 8);
        const formGroup = select.closest('.form-group');
        if (!formGroup) return;

        // Extract options from existing <select>
        const items = [];
        Array.from(select.options).forEach(function (opt) {
            if (!opt.value) return; // skip placeholder
            items.push({
                value: opt.value,
                label: opt.textContent.trim(),
                data: Object.assign({}, opt.dataset)
            });
        });

        const selectedValue = select.value;
        const selectedLabel = select.options[select.selectedIndex]
            ? select.options[select.selectedIndex].textContent.trim()
            : '';

        // Create DOM elements
        const wrapper = document.createElement('div');
        wrapper.className = 'bz-autocomplete';

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'bz-autocomplete-input';
        input.placeholder = options.placeholder || 'Buscar...';
        input.autocomplete = 'off';
        input.setAttribute('role', 'combobox');
        input.setAttribute('aria-expanded', 'false');
        input.setAttribute('aria-haspopup', 'listbox');
        input.setAttribute('aria-autocomplete', 'list');
        input.id = id + '_ac';

        const hidden = document.createElement('input');
        hidden.type = 'hidden';
        hidden.name = select.name;
        hidden.value = selectedValue;

        const list = document.createElement('div');
        list.className = 'bz-autocomplete-list';
        list.setAttribute('role', 'listbox');
        list.id = id + '_list';

        const clearBtn = document.createElement('button');
        clearBtn.type = 'button';
        clearBtn.className = 'bz-autocomplete-clear';
        clearBtn.innerHTML = '&times;';
        clearBtn.title = 'Limpiar selección';
        clearBtn.setAttribute('tabindex', '-1');

        // Copy attributes from original select
        if (select.required) hidden.required = true;
        if (select.dataset.required) hidden.dataset.required = select.dataset.required;
        select.removeAttribute('required');
        select.removeAttribute('data-required');

        // Replace select with autocomplete (keep select hidden for cloning)
        select.style.display = 'none';
        select.setAttribute('aria-hidden', 'true');
        select.disabled = true; // prevent duplicate form submission
        select.removeAttribute('name');
        wrapper.appendChild(input);
        wrapper.appendChild(clearBtn);
        wrapper.appendChild(hidden);
        wrapper.appendChild(list);
        select.parentNode.insertBefore(wrapper, select);

        // Set initial display
        if (selectedValue && selectedLabel) {
            input.value = selectedLabel.replace(/\s*\(.*\)\s*$/, ''); // clean trailing plates
            wrapper.classList.add('has-value');
        }

        // State
        let allItems = items.slice();
        let filteredItems = [];
        let selectedIndex = -1;
        let isOpen = false;
        let debounceTimer = null;

        // --- Filter & Render ---
        function filterItems(query) {
            if (!query) return allItems;
            const q = query.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
            return allItems.filter(function (item) {
                const label = item.label.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
                return label.indexOf(q) !== -1;
            });
        }

        function render(query) {
            filteredItems = filterItems(query);
            selectedIndex = -1;

            if (filteredItems.length === 0 && query) {
                list.innerHTML = '<div class="bz-ac-empty">Sin resultados para "<strong>' + escapeHTML(query) + '</strong>"</div>';
                openList();
                return;
            }

            if (filteredItems.length === 0) {
                closeList();
                return;
            }

            let html = '';
            filteredItems.forEach(function (item, i) {
                const highlighted = query ? highlightMatch(item.label, query) : escapeHTML(item.label);
                html += '<div class="bz-ac-option" role="option" data-index="' + i + '" data-value="' + item.value + '">' +
                    '<span class="bz-ac-option-text">' + highlighted + '</span>' +
                    '</div>';
            });
            list.innerHTML = html;
            openList();
        }

        function openList() {
            isOpen = true;
            list.classList.add('active');
            input.setAttribute('aria-expanded', 'true');
        }

        function closeList() {
            isOpen = false;
            list.classList.remove('active');
            input.setAttribute('aria-expanded', 'false');
            selectedIndex = -1;
        }

        function selectItem(index) {
            if (index < 0 || index >= filteredItems.length) return;
            const item = filteredItems[index];
            input.value = item.label.replace(/\s*\(.*\)\s*$/, '');
            hidden.value = item.value;
            wrapper.classList.add('has-value');
            closeList();
            input.blur();

            // Dispatch change event on hidden input
            hidden.dispatchEvent(new Event('change', { bubbles: true }));

            if (options.onChange) options.onChange(item.value, item);
        }

        function highlightIndex(index) {
            var options = list.querySelectorAll('.bz-ac-option');
            options.forEach(function (el, i) {
                el.classList.toggle('selected', i === index);
            });
            if (index >= 0 && options[index]) {
                options[index].scrollIntoView({ block: 'nearest' });
            }
            selectedIndex = index;
        }

        // --- Events ---
        input.addEventListener('input', function () {
            var query = this.value.trim();
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function () {
                render(query);
            }, 150);
        });

        input.addEventListener('focus', function () {
            var query = this.value.trim();
            if (allItems.length > 0) {
                render(query);
            }
        });

        input.addEventListener('keydown', function (e) {
            if (!isOpen) {
                if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                    e.preventDefault();
                    render(this.value.trim());
                    return;
                }
                return;
            }

            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    highlightIndex(Math.min(selectedIndex + 1, filteredItems.length - 1));
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    highlightIndex(Math.max(selectedIndex - 1, 0));
                    break;
                case 'Enter':
                    e.preventDefault();
                    if (selectedIndex >= 0) selectItem(selectedIndex);
                    break;
                case 'Escape':
                    closeList();
                    input.blur();
                    break;
            }
        });

        input.addEventListener('blur', function () {
            setTimeout(function () {
                closeList();
                // If input is empty, clear the hidden value (user removed selection)
                if (!input.value.trim()) {
                    hidden.value = '';
                    wrapper.classList.remove('has-value');
                } else if (!hidden.value && allItems.length > 0) {
                    // Try to match what user typed
                    var match = allItems.find(function (item) {
                        return item.label.toLowerCase().indexOf(input.value.trim().toLowerCase()) !== -1;
                    });
                    if (match) {
                        input.value = match.label.replace(/\s*\(.*\)\s*$/, '');
                        hidden.value = match.value;
                        wrapper.classList.add('has-value');
                        hidden.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                }
            }, 200);
        });

        // Click on option
        list.addEventListener('mousedown', function (e) {
            var option = e.target.closest('.bz-ac-option');
            if (option) {
                e.preventDefault();
                var idx = parseInt(option.dataset.index, 10);
                selectItem(idx);
            }
        });

        // Clear button
        clearBtn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            input.value = '';
            hidden.value = '';
            wrapper.classList.remove('has-value');
            input.focus();
            render('');
        });

        // --- AJAX reload (for dependent dropdowns) ---
        function loadAsync(parentId) {
            if (!options.async) return;
            var url = options.async.replace('{id}', parentId);
            input.disabled = true;
            input.value = 'Cargando...';
            hidden.value = '';
            wrapper.classList.remove('has-value');

            fetch(url)
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    allItems = data.map(function (item) {
                        return {
                            value: String(item.id),
                            label: item.marca
                                ? item.marca + ' ' + item.modelo + (item.placa ? ' (' + item.placa + ')' : '')
                                : item.nombre || item.label || String(item.id),
                            data: {}
                        };
                    });
                    input.value = '';
                    input.disabled = false;
                    input.placeholder = options.placeholder || 'Buscar...';
                })
                .catch(function () {
                    input.value = '';
                    input.disabled = false;
                    input.placeholder = 'Error al cargar';
                });
        }

        // Store instance
        var instance = {
            id: id,
            wrapper: wrapper,
            input: input,
            hidden: hidden,
            loadAsync: loadAsync,
            setItems: function (newItems) {
                allItems = newItems;
            },
            setValue: function (value, label) {
                hidden.value = value;
                input.value = label || '';
                if (value) {
                    wrapper.classList.add('has-value');
                } else {
                    wrapper.classList.remove('has-value');
                }
            }
        };
        instances[id] = instance;

        return instance;
    }

    function getInstance(id) {
        return instances[id] || null;
    }

    // --- Utilities ---
    function escapeHTML(str) {
        if (!str) return '';
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    function highlightMatch(text, query) {
        if (!text || !query) return escapeHTML(text || '');
        var escaped = escapeHTML(text);
        var q = escapeHTML(query);
        var regex = new RegExp('(' + q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
        return escaped.replace(regex, '<span class="bz-ac-highlight">$1</span>');
    }

    return {
        init: init,
        getInstance: getInstance
    };
})();
