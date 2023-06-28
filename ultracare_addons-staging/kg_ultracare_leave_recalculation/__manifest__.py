# -*- coding: utf-8 -*-
{
    'name': "Kg Employee Leave Recalculation",

    'summary': """
        Employee leave has to be recalculated if some public holidays get added in the later stage. """,

    'description': """
       Employee leave has to be recalculated if some public holidays get added in the later stage.
        Eg: employee took annual leave in a date rage where there is a public holiday.
    """,

    'author': "SHARMI SV",
    "license": "AGPL-3",
    'website': "http://www.klystronglobal.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Time off',
    'version': '16.0.0.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','hr_holidays'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/public_holiday_change_request_view.xml',
    ],

}
