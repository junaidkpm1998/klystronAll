# -*- coding: utf-8 -*-

{
    'name': "YGG Database Connector",
    'version': '16.0.1.0.0',
    'summary': """
        Inventory module updates""",
    'description': """ """,
    'author': "Klystron Global",
    'website': "http://www.klystronglobal.com",
    'depends': ['base', 'account', 'sale', 'vz_bankcharges'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',

        'views/res_company_view.xml',
        'views/ygg_currency_views.xml',
        'views/ygg_country_views.xml',
        'views/ygg_corporate_region_views.xml',
        'views/ygg_content_type_views.xml',
        'views/ygg_config_view.xml',
        'views/ygg_table_view.xml',
        'views/corporate_masters.xml',
        'views/res_partner_view.xml',
        'views/ygg_transaction_views.xml',
        'views/ygg_topup_views.xml',
        'views/ygg_gift_table_views.xml',
        'views/ygg_orders_order_views.xml',
        'views/res_config_settings_views.xml',
        'views/ygg_brand_commission_views.xml',
        'views/ygg_commission_conf_views.xml',
        'views/corporate_payment_views.xml',
        'views/rewards_corporate_gift_views_views.xml',
        'views/menu.xml',

        'wizard/sales_fetch_wizard_views.xml',

    ],
    'installable': True,
}
