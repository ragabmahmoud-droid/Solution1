# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError
from . import license_checker
import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        """Override to check user limit before creating users"""
        # First create the users
        users = super(ResUsers, self).create(vals_list)
        
        # Then check the limit if license validation is enabled
        if license_checker.is_enabled():
            max_users = license_checker.check_license(self.env, "users")
            
            if max_users is None:
                # Could not validate - allow by default or block based on policy
                _logger.warning("Could not validate user license, allowing creation")
                return users
            
            # Count current internal users (excluding portal/public users)
            # User ID 4 is typically OdooBot
            current_users = self.env["res.users"].sudo().search_count([
                ('active', '=', True),
                ('share', '=', False),  # Internal users only
                ('id', 'not in', [1, 4]),  # Exclude admin templates and OdooBot
            ])
            
            _logger.info("User limit check: current=%s, max=%s", current_users, max_users)
            
            if current_users > max_users:
                # Delete the just-created users
                created_count = len(users)
                users.sudo().unlink()
                raise UserError(_(
                    "Cannot create more users.\n\n"
                    "Current internal users: %s\n"
                    "Your license allows: %s users\n\n"
                    "Please contact your administrator to upgrade your license."
                ) % (current_users - created_count, max_users))
        
        return users

    def write(self, vals):
        """Check when activating users"""
        res = super(ResUsers, self).write(vals)
        
        # Check if activating users
        if vals.get('active') is True and license_checker.is_enabled():
            max_users = license_checker.check_license(self.env, "users")
            
            if max_users is not None:
                current_users = self.env["res.users"].sudo().search_count([
                    ('active', '=', True),
                    ('share', '=', False),
                    ('id', 'not in', [1, 4]),
                ])
                
                if current_users > max_users:
                    raise UserError(_(
                        "Cannot activate more users.\n\n"
                        "Current internal users: %s\n"
                        "Your license allows: %s users\n\n"
                        "Please deactivate other users or upgrade your license."
                    ) % (current_users, max_users))
        
        return res
