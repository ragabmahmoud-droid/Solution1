# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import UserError
from . import license_checker
import logging

_logger = logging.getLogger(__name__)


class IrModuleModule(models.Model):
    _inherit = 'ir.module.module'

    def _check_module_license(self):
        """Check if modules are allowed by license"""
        if not license_checker.is_enabled():
            return True
        
        # Skip check if called from license server (internal installation)
        if self._context.get('skip_license_check'):
            return True
        
        allowed_modules = license_checker.check_license(self.env, "modules")
        
        if allowed_modules is None:
            # Could not validate - log warning but allow
            _logger.warning("Could not validate module license, allowing installation")
            return True
        
        # Check if "all" is in the list (unlimited modules)
        if "all" in allowed_modules:
            return True
        
        # Check each module being installed
        blocked_modules = []
        for module in self:
            if module.name not in allowed_modules and module.name != 'asg_license_client':
                blocked_modules.append(module.name)
        
        if blocked_modules:
            raise UserError(_(
                "The following modules are not included in your license:\n\n"
                "• %s\n\n"
                "Allowed modules: %s\n\n"
                "Please contact your administrator to add these modules to your license."
            ) % ('\n• '.join(blocked_modules), ', '.join(sorted(allowed_modules))))
        
        return True

    def button_install(self):
        """Override to check license before installation"""
        self._check_module_license()
        return super(IrModuleModule, self).button_install()

    def button_immediate_install(self):
        """Override to check license before immediate installation"""
        self._check_module_license()
        return super(IrModuleModule, self).button_immediate_install()

    def button_uninstall(self):
        """Prevent uninstalling the license client module when enabled"""
        if license_checker.is_enabled():
            for module in self:
                if module.name == 'asg_license_client':
                    raise UserError(_(
                        "Cannot uninstall the License Client module while license validation is enabled.\n\n"
                        "To uninstall, first set 'enabled' to 'False' in the config.json file."
                    ))
        return super(IrModuleModule, self).button_uninstall()
