{
    'name': 'Associates products',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'sequence': -1,
    'installable': True,
    'application': True,
    'depends': ['base', 'sale_management', 'stock'],

    'data': [
        'views/res_partner_view.xml',
        'views/sale_order_view.xml'

    ]
}
