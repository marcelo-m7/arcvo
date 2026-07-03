/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";
import { NavBar } from "@web/webclient/navbar/navbar";

const DEFAULT_LAYOUT = {
    enabled: false,
    sidebarWidth: 360,
    compactMode: false,
    showQuickAccess: true,
    quickAccessLimit: 6,
    showAppIcons: true,
    logoUrl: "",
    accentColor: "#7c3aed",
    backgroundColor: "#111827",
};

function normalizeLayout(layout = {}) {
    return {
        ...DEFAULT_LAYOUT,
        ...layout,
        sidebarWidth: Number(layout.sidebarWidth || DEFAULT_LAYOUT.sidebarWidth),
        quickAccessLimit: Number(layout.quickAccessLimit || DEFAULT_LAYOUT.quickAccessLimit),
    };
}

function applyLayoutRootState(layout) {
    const config = normalizeLayout(layout);
    const root = document.documentElement;

    root.classList.toggle("o_custom_backend_layout_enabled", config.enabled);
    root.classList.toggle(
        "o_custom_backend_layout_compact",
        config.enabled && config.compactMode
    );
    root.classList.toggle(
        "o_custom_backend_layout_hide_icons",
        config.enabled && !config.showAppIcons
    );

    root.style.setProperty("--custom-backend-layout-sidebar-width", `${config.sidebarWidth}px`);
    root.style.setProperty("--custom-backend-layout-accent-color", config.accentColor);
    root.style.setProperty("--custom-backend-layout-background-color", config.backgroundColor);
}

function collectNavigableSections(sections, limit) {
    const items = [];

    function visit(sectionList) {
        for (const section of sectionList || []) {
            if (items.length >= limit) {
                return;
            }
            if (section.actionID || section.actionPath || !section.childrenTree?.length) {
                items.push(section);
            }
            if (section.childrenTree?.length) {
                visit(section.childrenTree);
            }
        }
    }

    visit(sections);
    return items;
}

applyLayoutRootState(session.custom_backend_layout);

patch(NavBar.prototype, {
    setup() {
        super.setup(...arguments);
        applyLayoutRootState(this.customBackendLayout);
    },

    get customBackendLayout() {
        return normalizeLayout(session.custom_backend_layout);
    },

    get customBackendLayoutQuickSections() {
        const layout = this.customBackendLayout;
        if (!layout.enabled || !layout.showQuickAccess || layout.quickAccessLimit <= 0) {
            return [];
        }
        return collectNavigableSections(this.currentAppSections, layout.quickAccessLimit);
    },
});
