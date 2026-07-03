FROM odoo:19

USER root
COPY --chown=odoo:odoo odoo/addons /mnt/extra-addons
COPY --chown=odoo:odoo odoo/external-addons/famebuilders/addons/custom_theme /mnt/extra-addons/custom_theme
USER odoo
