# -- coding: utf-8 --

{
    'name': "Analytic Distribution Widget",
    'summary': """Analytic Distribution Widget""",
    'description': """Analytic Distribution Widget""",
    'author': "",
    'website': "",
    'category': '',
    'version': '16.0.0.0.0',
    'depends': ['analytic', 'account'],
    'data': [
        'views/inherit_account_move.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'analytic_distribution_amount/static/src/js/analytic_distribution_widget.js',
            'analytic_distribution_amount/static/src/xml/analytic_distribution_widget.xml',
        ],

    },
    'installable': True,
    'application': True,
    'license': "AGPL-3",
}
