{
    'name': 'Payment PDF Report',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'sequence': -16,
    'installable': True,
    'application': True,
    'depends': ['base', 'account_accountant', 'stock','account'],

    'data': [
        'report/account_payment.xml',

    ]

}
