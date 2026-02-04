# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from . import license_checker
import logging

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    license_enabled = fields.Boolean(
        string="License Validation Enabled",
        readonly=True,
        help="Whether license validation is currently enabled (configured in config.json)"
    )
    license_server_url = fields.Char(
        string="License Server URL",
        readonly=True,
        help="The URL of the license server (configured in config.json)"
    )
    license_status = fields.Char(
        string="License Status",
        compute="_compute_license_status"
    )
    license_users_allowed = fields.Integer(
        string="Users Allowed",
        compute="_compute_license_info"
    )
    license_users_current = fields.Integer(
        string="Current Users",
        compute="_compute_license_info"
    )
    license_modules_allowed = fields.Text(
        string="Allowed Modules",
        compute="_compute_license_info"
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        config = license_checker.get_config()
        res.update(
            license_enabled=config.get('enabled', 'False') == 'True',
            license_server_url=config.get('license_server', ''),
        )
        return res

    @api.depends('license_enabled', 'license_server_url')
    def _compute_license_status(self):
        for record in self:
            if not record.license_enabled:
                record.license_status = _("Disabled - All features allowed")
            elif not record.license_server_url:
                record.license_status = _("Error - Server URL not configured")
            else:
                # Try to check connection
                test_result = license_checker.check_license(self.env, "users")
                if test_result is not None:
                    record.license_status = _("Connected - License active")
                else:
                    record.license_status = _("Error - Cannot connect to server")

    def _compute_license_info(self):
        for record in self:
            if license_checker.is_enabled():
                # Get users info
                users_allowed = license_checker.check_license(self.env, "users")
                record.license_users_allowed = users_allowed if users_allowed else 0
                
                record.license_users_current = self.env["res.users"].sudo().search_count([
                    ('active', '=', True),
                    ('share', '=', False),
                    ('id', 'not in', [1, 4]),
                ])
                
                # Get modules info
                modules = license_checker.check_license(self.env, "modules")
                if modules:
                    if "all" in modules:
                        record.license_modules_allowed = _("All modules allowed")
                    else:
                        record.license_modules_allowed = ", ".join(sorted(modules))
                else:
                    record.license_modules_allowed = _("Could not retrieve")
            else:
                record.license_users_allowed = 999999
                record.license_users_current = self.env["res.users"].sudo().search_count([
                    ('active', '=', True),
                    ('share', '=', False),
                    ('id', 'not in', [1, 4]),
                ])
                record.license_modules_allowed = _("All modules allowed (validation disabled)")

    def action_reload_license_config(self):
        """Reload the license configuration from config.json"""
        license_checker.reload_config()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('License Configuration'),
                'message': _('Configuration reloaded successfully'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_test_license_connection(self):
        """Test connection to the license server"""
        if not license_checker.is_enabled():
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('License Connection'),
                    'message': _('License validation is disabled'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        result = license_checker.check_license(self.env, "users")
        if result is not None:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('License Connection'),
                    'message': _('Connection successful! Users allowed: %s') % result,
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('License Connection'),
                    'message': _('Could not connect to license server'),
                    'type': 'danger',
                    'sticky': False,
                }
            }
