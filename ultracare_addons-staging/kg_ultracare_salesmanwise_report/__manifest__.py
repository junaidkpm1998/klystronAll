# -*- coding: utf-8 -*-
{
    'name': "kg_ultracare_salesmanwise_report",

    'summary': """Salesperson wise groupby partners invoice""",

    "version": "16.0.1.0.0",

    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    'website': "https://www.klystronglobal.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',

        'report/statement_report.xml',

        'views/views.xml',
        'views/templates.xml',

        'wizard/statement_report_wizard.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
