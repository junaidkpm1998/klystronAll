# -*- coding: utf-8 -*-
{
    'name': "KG : Accounts",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "SHARMI SV",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.00.00',

    # any module necessary for this one to work correctly
    'depends': ['base','account','membership','account_batch_payment'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/bank_statement_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}