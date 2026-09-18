// BikerZone - Main JavaScript

(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        initThemeToggle();
        initSidebar();
        initMobileMenu();
        initGlobalSearch();
        initMobileSearch();
        initAutoAlerts();
        initModals();
        initFormValidation();
        initKPIAnimation();
        initClickableRows();
        initLiveFiltering();
        initTextareaAutoResize();
    });

    // --- Theme Toggle ---
    function initThemeToggle() {
        const themeToggle = document.getElementById('theme-toggle');
        const html = document.documentElement;
        const savedTheme = localStorage.getItem('theme') || 'light';
        html.setAttribute('data-theme', savedTheme);

        if (themeToggle) {
            themeToggle.addEventListener('click', function () {
                const current = html.getAttribute('data-theme');
                const next = current === 'dark' ? 'light' : 'dark';
                html.setAttribute('data-theme', next);
                localStorage.setItem('theme', next);
            });
        }
    }

    // --- Sidebar ---
    function initSidebar() {
        const sidebar = document.getElementById('sidebar');
        const sidebarToggle = document.getElementById('sidebar-toggle');
        const collapsed = localStorage.getItem('sidebar-collapsed') === 'true';

        if (collapsed && sidebar) {
            sidebar.classList.add('collapsed');
        }

        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', function () {
                sidebar.classList.toggle('collapsed');
                localStorage.setItem('sidebar-collapsed', sidebar.classList.contains('collapsed'));
            });
        }
    }

    // --- Mobile Menu ---
    function initMobileMenu() {
        const mobileMenuBtn = document.getElementById('mobile-menu-btn');
        const mobileOverlay = document.getElementById('mobile-overlay');
        const sidebar = document.getElementById('sidebar');

        function openMobileMenu() {
            sidebar.classList.add('mobile-open');
            mobileOverlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }

        function closeMobileMenu() {
            sidebar.classList.remove('mobile-open');
            mobileOverlay.classList.remove('active');
            document.body.style.overflow = '';
        }

        if (mobileMenuBtn) {
            mobileMenuBtn.addEventListener('click', openMobileMenu);
        }

        if (mobileOverlay) {
            mobileOverlay.addEventListener('click', closeMobileMenu);
        }

        document.querySelectorAll('.sidebar-link').forEach(function (link) {
            link.addEventListener('click', function () {
                if (window.innerWidth <= 768) {
                    closeMobileMenu();
                }
            });
        });
    }

    // --- Global Search (Desktop) ---
    function initGlobalSearch() {
        const globalSearch = document.getElementById('global-search');
        if (!globalSearch) return;

        const searchWrapper = globalSearch.closest('.topbar-search');
        const searchResults = createSearchDropdown();
        searchWrapper.appendChild(searchResults);

        // Add loading spinner element
        const spinner = document.createElement('div');
        spinner.className = 'search-loading';
        searchWrapper.appendChild(spinner);

        let searchTimeout = null;
        let selectedIndex = -1;
        let currentResults = [];

        globalSearch.addEventListener('input', function () {
            const query = this.value.trim();
            clearTimeout(searchTimeout);
            selectedIndex = -1;
            currentResults = [];

            if (query.length < 2) {
                searchResults.classList.remove('active');
                searchWrapper.classList.remove('loading');
                return;
            }

            searchWrapper.classList.add('loading');

            searchTimeout = setTimeout(function () {
                fetch('/api/search?q=' + encodeURIComponent(query))
                    .then(function (response) { return response.json(); })
                    .then(function (data) {
                        searchWrapper.classList.remove('loading');
                        if (data.results && data.results.length > 0) {
                            currentResults = data.results;
                            renderGroupedResults(searchResults, data.results, query);
                            searchResults.classList.add('active');
                        } else {
                            searchResults.innerHTML =
                                '<div class="search-no-results">' +
                                '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">' +
                                '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>' +
                                '</svg>' +
                                'No se encontraron resultados para "<strong>' + escapeHTML(query) + '</strong>"' +
                                '</div>';
                            searchResults.classList.add('active');
                        }
                    })
                    .catch(function () {
                        searchWrapper.classList.remove('loading');
                        searchResults.classList.remove('active');
                    });
            }, 300);
        });

        // Keyboard navigation
        globalSearch.addEventListener('keydown', function (e) {
            const items = searchResults.querySelectorAll('.search-result-item');
            if (!items.length) return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
                highlightSearchItem(items, selectedIndex);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                selectedIndex = Math.max(selectedIndex - 1, -1);
                highlightSearchItem(items, selectedIndex);
            } else if (e.key === 'Enter' && selectedIndex >= 0) {
                e.preventDefault();
                const link = items[selectedIndex].getAttribute('href');
                if (link) window.location.href = link;
            }
        });

        // Close on blur with safe delay
        globalSearch.addEventListener('blur', function () {
            setTimeout(function () {
                searchResults.classList.remove('active');
                searchWrapper.classList.remove('loading');
            }, 250);
        });

        globalSearch.addEventListener('focus', function () {
            if (searchResults.children.length > 0 && this.value.trim().length >= 2) {
                searchResults.classList.add('active');
            }
        });

        // Ctrl+K / Cmd+K shortcut
        document.addEventListener('keydown', function (e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                globalSearch.focus();
                globalSearch.select();
            }
            if (e.key === 'Escape') {
                globalSearch.blur();
                searchResults.classList.remove('active');
            }
        });
    }

    // --- Mobile Search (FAB + Modal) ---
    function initMobileSearch() {
        const fab = document.querySelector('.mobile-search-fab');
        const modal = document.querySelector('.mobile-search-modal');
        if (!fab || !modal) return;

        const modalInput = modal.querySelector('.mobile-search-input');
        const modalResults = modal.querySelector('.mobile-search-results');
        const closeBtn = modal.querySelector('.mobile-search-close-btn');

        let searchTimeout = null;

        fab.addEventListener('click', function () {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
            setTimeout(function () { modalInput.focus(); }, 100);
        });

        function closeModal() {
            modal.classList.remove('active');
            document.body.style.overflow = '';
            modalInput.value = '';
            modalResults.innerHTML = '';
        }

        if (closeBtn) closeBtn.addEventListener('click', closeModal);

        modal.addEventListener('click', function (e) {
            if (e.target === modal) closeModal();
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && modal.classList.contains('active')) {
                closeModal();
            }
        });

        modalInput.addEventListener('input', function () {
            const query = this.value.trim();
            clearTimeout(searchTimeout);

            if (query.length < 2) {
                modalResults.innerHTML = '';
                return;
            }

            searchTimeout = setTimeout(function () {
                fetch('/api/search?q=' + encodeURIComponent(query))
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        if (data.results && data.results.length > 0) {
                            renderGroupedResults(modalResults, data.results, query);
                        } else {
                            modalResults.innerHTML =
                                '<div class="search-no-results">No se encontraron resultados</div>';
                        }
                    })
                    .catch(function () {
                        modalResults.innerHTML = '';
                    });
            }, 300);
        });
    }

    // --- Search Rendering Helpers ---
    function createSearchDropdown() {
        const div = document.createElement('div');
        div.className = 'search-results';
        return div;
    }

    function renderGroupedResults(container, results, query) {
        const groups = {};
        const typeOrder = ['cliente', 'moto', 'orden', 'repuesto', 'proveedor'];
        const typeLabels = {
            cliente: 'Clientes',
            moto: 'Motos',
            orden: 'Ordenes de Servicio',
            repuesto: 'Repuestos',
            proveedor: 'Proveedores'
        };

        results.forEach(function (item) {
            if (!groups[item.type]) groups[item.type] = [];
            groups[item.type].push(item);
        });

        let html = '';
        typeOrder.forEach(function (type) {
            if (!groups[type] || !groups[type].length) return;
            html += '<div class="search-category-header">' + typeLabels[type] + '</div>';
            groups[type].forEach(function (item) {
                const highlightedTitle = highlightMatch(item.title, query);
                const highlightedSubtitle = highlightMatch(item.subtitle, query);
                html +=
                    '<a href="' + item.url + '" class="search-result-item">' +
                    '<div class="search-result-icon" data-type="' + item.type + '">' + getItemIcon(item.type) + '</div>' +
                    '<div class="search-result-info">' +
                    '<div class="search-result-title">' + highlightedTitle + '</div>' +
                    '<div class="search-result-subtitle">' + highlightedSubtitle + '</div>' +
                    '</div></a>';
            });
        });

        container.innerHTML = html;
    }

    function highlightMatch(text, query) {
        if (!text || !query) return escapeHTML(text || '');
        const escaped = escapeHTML(text);
        const queryEscaped = escapeHTML(query);
        const regex = new RegExp('(' + escapeRegex(queryEscaped) + ')', 'gi');
        return escaped.replace(regex, '<span class="search-highlight">$1</span>');
    }

    function highlightSearchItem(items, index) {
        items.forEach(function (item, i) {
            item.classList.toggle('selected', i === index);
        });
        if (index >= 0 && items[index]) {
            items[index].scrollIntoView({ block: 'nearest' });
        }
    }

    function getItemIcon(type) {
        const icons = {
            cliente: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
            moto: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="5" cy="18" r="3"/><circle cx="19" cy="18" r="3"/><path d="M12 18V6l-4 6h8"/></svg>',
            orden: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
            repuesto: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>',
            proveedor: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12h4l2-9 5 18 2-9h5"/></svg>'
        };
        return icons[type] || icons.orden;
    }

    // --- Auto-dismiss Alerts ---
    function initAutoAlerts() {
        document.querySelectorAll('.alert').forEach(function (alert) {
            setTimeout(function () {
                alert.style.opacity = '0';
                alert.style.transition = 'opacity 0.3s ease';
                setTimeout(function () { alert.remove(); }, 300);
            }, 5000);
        });
    }

    // --- Modals ---
    function initModals() {
        document.querySelectorAll('[data-modal]').forEach(function (trigger) {
            trigger.addEventListener('click', function (e) {
                e.preventDefault();
                const modal = document.getElementById(this.getAttribute('data-modal'));
                if (modal) modal.classList.add('active');
            });
        });

        document.querySelectorAll('.modal-overlay').forEach(function (overlay) {
            overlay.addEventListener('click', function (e) {
                if (e.target === this) this.classList.remove('active');
            });
        });

        document.querySelectorAll('[data-close-modal]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                this.closest('.modal-overlay').classList.remove('active');
            });
        });
    }

    // --- Form Validation + Submit Loading (unified) ---
    function initFormValidation() {
        document.querySelectorAll('form').forEach(function (form) {
            form.addEventListener('submit', function (e) {
                let valid = true;

                form.querySelectorAll('[required]').forEach(function (field) {
                    if (field.disabled || field.type === 'hidden') return;
                    const group = field.closest('.form-group');
                    if (!field.value.trim()) {
                        valid = false;
                        if (group) {
                            group.classList.add('error');
                            if (!group.querySelector('.error-message')) {
                                var msg = document.createElement('span');
                                msg.className = 'error-message';
                                msg.textContent = 'Este campo es requerido';
                                group.appendChild(msg);
                            }
                        }
                        field.setAttribute('aria-invalid', 'true');
                    } else {
                        if (group) {
                            group.classList.remove('error');
                            var existingMsg = group.querySelector('.error-message');
                            if (existingMsg) existingMsg.remove();
                        }
                        field.removeAttribute('aria-invalid');
                    }
                });

                if (!valid) {
                    e.preventDefault();
                    const firstInvalid = form.querySelector('[aria-invalid="true"]');
                    if (firstInvalid) {
                        firstInvalid.focus();
                        firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                    return; // do NOT set loading state
                }

                // Validation passed — show loading state
                const submitBtn = this.querySelector('button[type="submit"]');
                if (submitBtn && !submitBtn.dataset.loading) {
                    submitBtn.dataset.originalText = submitBtn.innerHTML;
                    submitBtn.innerHTML =
                        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: bzspin 1s linear infinite;">' +
                        '<circle cx="12" cy="12" r="10" stroke-dasharray="50" stroke-dashoffset="20"/></svg> Guardando...';
                    submitBtn.disabled = true;
                    submitBtn.dataset.loading = 'true';
                }
            });

            // Clear error on input
            form.querySelectorAll('[required]').forEach(function (field) {
                field.addEventListener('input', function () {
                    const group = this.closest('.form-group');
                    if (group && group.classList.contains('error') && this.value.trim()) {
                        group.classList.remove('error');
                        this.removeAttribute('aria-invalid');
                    }
                });
            });
        });

        // Inject spin keyframes once
        if (!document.getElementById('bz-spin-style')) {
            const style = document.createElement('style');
            style.id = 'bz-spin-style';
            style.textContent = '@keyframes bzspin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }';
            document.head.appendChild(style);
        }
    }

    // --- KPI Value Animation ---
    function initKPIAnimation() {
        document.querySelectorAll('.kpi-value').forEach(function (el) {
            const text = el.textContent;
            const match = text.match(/^([^0-9]*)([0-9,.]+)(.*)$/);
            if (!match) return;

            const prefix = match[1];
            const numStr = match[2].replace(/,/g, '');
            const suffix = match[3];
            const target = parseFloat(numStr);

            if (isNaN(target) || target <= 0) return;

            const duration = 1000;
            let startTime = null;

            function animate(currentTime) {
                if (!startTime) startTime = currentTime;
                const progress = Math.min((currentTime - startTime) / duration, 1);
                const eased = 1 - Math.pow(1 - progress, 3);
                const current = Math.floor(eased * target);

                el.textContent = prefix + (target >= 1000 ? current.toLocaleString() : current) + suffix;

                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    el.textContent = text;
                }
            }

            el.textContent = prefix + '0' + suffix;
            requestAnimationFrame(animate);
        });
    }

    // --- Clickable Table Rows ---
    function initClickableRows() {
        document.querySelectorAll('tbody tr[data-href]').forEach(function (row) {
            row.addEventListener('click', function (e) {
                if (e.target.closest('a, button')) return;
                window.location.href = this.dataset.href;
            });
        });
    }

    // --- Live Filtering (debounced search inputs in filter forms) ---
    function initLiveFiltering() {
        document.querySelectorAll('.filters input[type="text"], .filters input[type="search"]').forEach(function (input) {
            let timeout = null;
            input.addEventListener('input', function () {
                clearTimeout(timeout);
                const form = this.closest('form');
                if (!form) return;
                timeout = setTimeout(function () {
                    // Update URL params without full reload
                    const formData = new FormData(form);
                    const params = new URLSearchParams(window.location.search);
                    formData.forEach(function (value, key) {
                        if (value) {
                            params.set(key, value);
                        } else {
                            params.delete(key);
                        }
                    });
                    params.set('page', '1');
                    const newURL = window.location.pathname + '?' + params.toString();
                    window.location.href = newURL;
                }, 500);
            });
        });
    }

    // --- Textarea Auto-Resize ---
    function initTextareaAutoResize() {
        document.querySelectorAll('textarea').forEach(function (textarea) {
            // Set initial height based on content
            autoResize(textarea);

            // Resize on input
            textarea.addEventListener('input', function () {
                autoResize(this);
            });
        });

        function autoResize(el) {
            // Reset height to auto to get the correct scrollHeight
            el.style.height = 'auto';
            // Set height to scrollHeight, capped by max-height from CSS
            var newHeight = Math.min(el.scrollHeight, parseInt(getComputedStyle(el).maxHeight) || 300);
            el.style.height = newHeight + 'px';
        }
    }

    // --- Utility ---
    function escapeHTML(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    function escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
})();

// --- Toast Notification (global) ---
function showToast(message, type) {
    type = type || 'success';
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const icons = {
        success: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        danger: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        warning: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
    };

    const toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.innerHTML = (icons[type] || '') + '<span>' + message + '</span>';
    container.appendChild(toast);

    setTimeout(function () {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(function () { toast.remove(); }, 300);
    }, 4000);
}

// --- Confirm Delete (safe DOM-based, no XSS) ---
function confirmDelete(message) {
    return new Promise(function (resolve) {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay active';

        const modal = document.createElement('div');
        modal.className = 'modal';

        const header = document.createElement('div');
        header.className = 'modal-header';
        const h3 = document.createElement('h3');
        h3.textContent = 'Confirmar eliminación';
        header.appendChild(h3);

        const body = document.createElement('div');
        body.className = 'modal-body';
        const p = document.createElement('p');
        p.textContent = message || '¿Estás seguro de que deseas eliminar este elemento?';
        body.appendChild(p);

        const footer = document.createElement('div');
        footer.className = 'modal-footer';

        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'btn btn-secondary';
        cancelBtn.textContent = 'Cancelar';

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-danger';
        deleteBtn.textContent = 'Eliminar';

        footer.appendChild(cancelBtn);
        footer.appendChild(deleteBtn);
        modal.appendChild(header);
        modal.appendChild(body);
        modal.appendChild(footer);
        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        function close(result) {
            overlay.remove();
            resolve(result);
        }

        cancelBtn.addEventListener('click', function () { close(false); });
        deleteBtn.addEventListener('click', function () { close(true); });
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) close(false);
        });
    });
}
