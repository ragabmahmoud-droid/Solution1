# -*- coding: utf-8 -*-
{
    'name': "License Client",
    'summary': "Validates users count and allowed modules against license server",
    'description': """
        License Client for SaaS Management
        ===================================
        
        This module validates the client instance against the license server:
        - Checks maximum users count when creating new users
        - Validates module installation against allowed modules list
        - Prevents uninstalling the license module when enabled
        
        Configuration:
        -------------
        Edit config.json file in the module directory:
        {
            "enabled": "True",
            "license_server": "http://your-server:port"
        }
        
        API Endpoint:
        ------------
        The module connects to /se_license/check on the license server
    """,
    'author': "SE",
    'website': "",
    'category': 'Technical',
    'version': '18.0.1.0.0',
    'depends': ['base'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
