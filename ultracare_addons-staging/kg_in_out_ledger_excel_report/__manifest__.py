# -*- coding: utf-8 -*-
{
    'name': "kg_in_out_ledger_excel_report",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "SHARMI SV",
    'website': "https://www.klystronglobal.com",
    'version': '16.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','kg_ultracare_inventory'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'kg_in_out_ledger_excel_report/static/src/js/action_manager.js',
        ]
    },
    'application': True,
}
