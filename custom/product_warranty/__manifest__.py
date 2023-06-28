{
    'name': 'Product Warranty',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'sequence': -16,
    'installable': True,
    'application': True,
    'depends': ['base', 'sale_management', 'stock'],

    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'wizard/warranty_wizard.xml',
        'report/warranty_report.xml',
        'data/location.xml',
        'views/invoice_page.xml',
        # 'views/warranty_web.xml',
        'views/warranty_template.xml',
        'views/warranty_views.xml',
        'views/product_form.xml',
        'views/warranty_menu.xml',

    ],

    'assets': {
        'web.assets_backend': [
            'product_warranty/static/src/js/action_manager.js'
        ],
        'web.assets_frontend': [
            'product_warranty/static/src/js/warranty.js'
        ],

    }
}
