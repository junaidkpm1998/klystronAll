{
    'name': 'Material Request',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'sequence': -1,
    'installable': True,
    'application': True,
    'depends': ['base', 'product', 'stock', 'purchase'],

    'data': [
        'security/ir.model.access.csv',
        'views/material_request_view.xml',
        'views/purchase_order_view.xml',
        'wizard/wizard_view.xml',
        'views/menu.xml'

    ]

}
