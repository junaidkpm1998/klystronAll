# -*- coding: utf-8 -*-

{
    'name': "Inventory Updates",
    'version': '16.0.1.0.0',
    'summary': """
        Inventory module updates""",
    'description': """
    """,
    'author': "Klystron Global",
    'website': "http://www.klystronglobal.com",
    'depends': ['account', 'stock', 'hr', 'product','purchase', 'vz_bankcharges'],
    'data': [
        'security/ir.model.access.csv',
        'data/journal_data.xml',
        'views/product_view.xml',
        'views/ygg_adv_payment_views.xml',
        'views/res_config_settings_view.xml',
        'views/partner_view.xml',
        # 'views/account_move_views.xml',
        'views/product_supplierinfo.xml',
    ],
    'installable': True,
}
