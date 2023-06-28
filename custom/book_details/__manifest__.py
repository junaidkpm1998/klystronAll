{
    'name': 'Book Details',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'sequence': -1,
    'installable': True,
    'application': True,
    'depends': ['base', 'stock', 'sale_management'],

    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/action.xml',
        'views/res_partner.xml',
        'views/product_product.xml',
        'views/product_resesrvation.xml',
        'data/cron.xml',
        'views/menu.xml'

    ]

}
