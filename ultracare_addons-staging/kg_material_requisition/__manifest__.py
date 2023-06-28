# -*- coding: utf-8 -*-
{
    'name': "Kg Material Requisition",

    'summary': """
        Form for raw material Requisition""",

    'description': """
        Form for raw material Requisition
    """,

    'author': "MINI K",
    'website': "http://www.klystronglobal.com",

    'category': 'Uncategorized',
    'version': '15.0.0.0',
    "license": "AGPL-3",

    # any module necessary for this one to work correctly
    'depends': ['base','stock','mail','mrp'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/approval_template.xml',
        'views/requisition.xml',
        'views/res_config.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
