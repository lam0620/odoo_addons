# -*- coding: utf-8 -*-
###################################################################################

###################################################################################
{
    'name': 'Spa Management',
    'summary': 'Spa Management with Online Booking System',
    'version': '16.0.1.0.0',
    'author': 'Sprite plus',
    'company': 'Sprite plus',
    'license': 'AGPL-3',    
    'installable': True,
    'application': True,    
    "category": "Industries",
    'depends': ['account', 'base', 'base_setup', 'mail', 'website', 'contacts', 'calendar', 'web','hr','website_sale'],
    'data': [
        'security/spa_management_groups.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/mail_template.xml',
        'data/spa_chair_data.xml',
        'data/spa_holiday_data.xml',
        'data/spa_working_hours_data.xml',
        'data/spa_source_data.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        'views/spa_booking_service_templates.xml',
        'views/spa_booking_views.xml',
        'views/spa_order_views.xml',
        'views/spa_chairs.xml',
        'views/spa_management_views.xml',
        'views/spa_product_service.xml',
        'views/spa_management_menus.xml',
        'views/spa_booking_history_views.xml',
        'views/spa_website_sale_booking_templates.xml',
        'views/hr_employee_views.xml',
    ],
    'images': [''],
    'assets': {
        'web.assets_backend': [
            'spa_management/static/src/css/spa_dashboard.css',
            'spa_management/static/src/xml/spa_dashboard.xml',
            'spa_management/static/src/js/spa_dashboard.js',
            'spa_management/static/src/js/custom.js',
        ],
        'web.assets_frontend': [
            'spa_management/static/src/css/spa_website.css',
            'spa_management/static/src/js/website_spa_booking.js',
            'spa_management/static/src/js/website_spa_booking_service.js',
        ],
    },
}
