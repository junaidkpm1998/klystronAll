# -*- coding: utf-8 -*-
{
    'name': "KG Sale",
    'version': '16.0.1.0.0',

    'summary': """
        This module is all about sale order report action and partner field""",

    'description': """
        This module has the following functionalities
        1) Partner type field added in res.partner model
        2) Hide the existing report action from sale order
        3) add a button in status bar for quotation report print
    """,

    'author': "Klystron",
    'website': "http://www.klystronglobal.com",

    'category': 'Uncategorized',

    'depends': ['base', 'sale_management', 'contacts', 'hr', 'sale'],

    'data': [
        'security/ir.model.access.csv',
        'data/sale_sequence.xml',
        'views/sale_order_view.xml',
        'views/category_views.xml',
        'views/partner_view.xml',
        'views/product_view.xml',
        'views/hr_employee_view.xml',
        'reports/sale_report_template.xml',
        'reports/quotation_report_template.xml',
        'reports/report.xml',
    ],

}
