{
    'name': 'Automatic Sale Order',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'sequence': -1,
    'installable': True,
    'application': True,
    'depends': ['base', 'sale_management', 'stock'],

    'data': [
        'security/ir.model.access.csv',
        'views/product_template.xml',
        'wizard/automatic_so_wizard.xml'
    ]

}