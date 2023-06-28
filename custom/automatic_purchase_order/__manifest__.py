{
    'name': 'Automatic purchase Order',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'sequence': -1,
    'installable': True,
    'application': True,
    'depends': ['base', 'sale_management','purchase', 'stock'],

    'data': [
        'security/ir.model.access.csv',
        'view/product_product.xml',
        'wizard/automatic_po_wizard.xml'

    ]

}