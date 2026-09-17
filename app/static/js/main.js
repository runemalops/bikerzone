// BikerZone - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Theme Toggle
    const themeToggle = document.getElementById('theme-toggle');
    const html = document.documentElement;
    const savedTheme = localStorage.getItem('theme') || 'light';
    html.setAttribute('data-theme', savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }

    // Sidebar Toggle
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebarCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';

    if (sidebarCollapsed && sidebar) {
        sidebar.classList.add('collapsed');
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            localStorage.setItem('sidebar-collapsed', sidebar.classList.contains('collapsed'));
        });
    }

    // Mobile Menu
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileOverlay = document.getElementById('mobile-overlay');

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

    document.querySelectorAll('.sidebar-link').forEach(function(link) {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                closeMobileMenu();
            }
        });
    });

    // Global Search
    const globalSearch = document.getElementById('global-search');
    const searchResults = document.createElement('div');
    searchResults.className = 'search-results';
    if (globalSearch) {
        globalSearch.parentNode.appendChild(searchResults);
    }

    let searchTimeout = null;

    if (globalSearch) {
        globalSearch.addEventListener('input', function() {
            const query = this.value.trim();
            clearTimeout(searchTimeout);

            if (query.length < 2) {
                searchResults.classList.remove('active');
                return;
            }

            searchTimeout = setTimeout(function() {
                fetch('/api/search?q=' + encodeURIComponent(query))
                    .then(function(response) { return response.json(); })
                    .then(function(data) {
                        if (data.results && data.results.length > 0) {
                            let html = '';
                            data.results.forEach(function(item) {
                                html += '<a href="' + item.url + '" class="search-result-item">';
                                html += '<div class="search-result-icon">' + getItemIcon(item.type) + '</div>';
                                html += '<div class="search-result-info">';
                                html += '<div class="search-result-title">' + item.title + '</div>';
                                html += '<div class="search-result-subtitle">' + item.subtitle + '</div>';
                                html += '</div></a>';
                            });
                            searchResults.innerHTML = html;
                            searchResults.classList.add('active');
                        } else {
                            searchResults.innerHTML = '<div class="search-no-results">No se encontraron resultados</div>';
                            searchResults.classList.add('active');
                        }
                    })
                    .catch(function() {
                        searchResults.classList.remove('active');
                    });
            }, 300);
        });

        globalSearch.addEventListener('blur', function() {
            setTimeout(function() {
                searchResults.classList.remove('active');
            }, 200);
        });

        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                globalSearch.focus();
            }
            if (e.key === 'Escape') {
                globalSearch.blur();
                searchResults.classList.remove('active');
            }
        });
    }

    function getItemIcon(type) {
        var icons = {
            cliente: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
            moto: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="5" cy="18" r="3"/><circle cx="19" cy="18" r="3"/><path d="M12 18V6l-4 6h8"/></svg>',
            orden: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
            repuesto: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>'
        };
        return icons[type] || icons.orden;
    }

    // Auto-dismiss alerts
    document.querySelectorAll('.alert').forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.3s ease';
            setTimeout(function() { alert.remove(); }, 300);
        }, 5000);
    });

    // Modal functionality
    document.querySelectorAll('[data-modal]').forEach(function(trigger) {
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            var modalId = this.getAttribute('data-modal');
            var modal = document.getElementById(modalId);
            if (modal) { modal.classList.add('active'); }
        });
    });

    document.querySelectorAll('.modal-overlay').forEach(function(overlay) {
        overlay.addEventListener('click', function(e) {
            if (e.target === this) { this.classList.remove('active'); }
        });
    });

    document.querySelectorAll('[data-close-modal]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            this.closest('.modal-overlay').classList.remove('active');
        });
    });

    // Form validation
    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            var requiredFields = form.querySelectorAll('[required]');
            var valid = true;

            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    field.style.borderColor = 'var(--color-danger)';
                    valid = false;
                } else {
                    field.style.borderColor = '';
                }
            });

            if (!valid) { e.preventDefault(); }
        });
    });

    // Animate KPI values
    document.querySelectorAll('.kpi-value').forEach(function(el) {
        var text = el.textContent;
        var match = text.match(/^([^0-9]*)([0-9,.]+)(.*)$/);
        if (match) {
            var prefix = match[1];
            var numStr = match[2].replace(/,/g, '');
            var suffix = match[3];
            var target = parseFloat(numStr);

            if (!isNaN(target) && target > 0) {
                var duration = 1000;
                var start = 0;
                var startTime = null;

                function animate(currentTime) {
                    if (!startTime) startTime = currentTime;
                    var progress = Math.min((currentTime - startTime) / duration, 1);
                    var eased = 1 - Math.pow(1 - progress, 3);
                    var current = Math.floor(eased * target);

                    if (target >= 1000) {
                        el.textContent = prefix + current.toLocaleString() + suffix;
                    } else {
                        el.textContent = prefix + current + suffix;
                    }

                    if (progress < 1) {
                        requestAnimationFrame(animate);
                    } else {
                        el.textContent = text;
                    }
                }

                el.textContent = prefix + '0' + suffix;
                requestAnimationFrame(animate);
            }
        }
    });
});

// Toast notification function
function showToast(message, type) {
    type = type || 'success';
    var container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    var icons = {
        success: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        danger: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        warning: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
    };

    var toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.innerHTML = (icons[type] || '') + '<span>' + message + '</span>';
    container.appendChild(toast);

    setTimeout(function() {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(function() { toast.remove(); }, 300);
    }, 4000);
}

// Confirm delete helper
function confirmDelete(message) {
    return new Promise(function(resolve) {
        var overlay = document.createElement('div');
        overlay.className = 'modal-overlay active';
        overlay.innerHTML = '<div class="modal">' +
            '<div class="modal-header"><h3>Confirmar eliminación</h3></div>' +
            '<div class="modal-body"><p>' + (message || '¿Estás seguro de que deseas eliminar este elemento?') + '</p></div>' +
            '<div class="modal-footer">' +
            '<button class="btn btn-secondary" data-close-modal>Cancelar</button>' +
            '<button class="btn btn-danger" id="confirm-delete-btn">Eliminar</button>' +
            '</div></div>';

        document.body.appendChild(overlay);

        overlay.querySelector('[data-close-modal]').addEventListener('click', function() {
            overlay.remove();
            resolve(false);
        });

        overlay.querySelector('#confirm-delete-btn').addEventListener('click', function() {
            overlay.remove();
            resolve(true);
        });

        overlay.addEventListener('click', function(e) {
            if (e.target === this) {
                overlay.remove();
                resolve(false);
            }
        });
    });
}
