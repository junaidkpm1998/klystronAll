{
    'name': 'POS A4 Print',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'sequence': -1,
    'installable': True,
    'application': True,
    'depends': ['base', 'point_of_sale'],

    'data': [

    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_a4_print/static/src/js/invoice_print.js',
            'pos_a4_print/static/src/xml/invoice_print.xml',
        ],
    },

}
