{
    'name': 'Customer Credit Limit With Due Amount Warning',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'sequence': -16,
    'installable': True,
    'application': True,
    'depends': ['base', 'contacts', 'account_accountant', 'sale_management'],

    'data': [
        'views/res_partner_views.xml',
    ]

}
