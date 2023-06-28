# -*- coding: utf-8 -*-
{
    'name': "kg_ultracare_sale",

    "summary": "Sales and CRM modules",
    "version": "16.0.1.0.0",
    'category': 'Sales/CRM',
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',
    # any module necessary for this one to work correctly
    'depends': ['base', 'phone_validation', 'sale_management', 'sale_crm', 'mail', 'crm', 'account', 'web', 'stock', 'product',
                'kg_material_requisition', 'sale_stock', 'kg_ultracare_inventory','account_followup','calendar','knowledge'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/kg_data.xml',
        'data/sequence.xml',
        'data/paper_format.xml',

        'report/report.xml',
        'report/delivery_note_report.xml',
        'report/tax_invoice_report.xml',
        'report/purchase_returns_report.xml',
        'report/sales_returns_report.xml',
        'report/invoice_report_inherit_views.xml',
        'report/quotation_order_report_inherit_view.xml',
        'report/sale_quotation_report.xml',
        'report/customer_analysis_report.xml',
        'report/sale_analysis_report.xml',
        'report/sale_details_report.xml',
        'report/profitability_report.xml',
        'report/sales_register_report.xml',
        'report/proforma_invoice_inherit_report.xml',

        'wizard/sale_analysis_wizard.xml',
        'wizard/customer_analysis_wizard.xml',
        'wizard/sales_quotation_wizard.xml',
        'wizard/sales_details_wizard.xml',
        'wizard/profitability_analysis_wizard.xml',
        'wizard/sales_register_wizard.xml',

        'views/sale_views.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/account_moves_views.xml',
        'views/crm_views.xml',
        'views/res_partner_views.xml',
        'views/res_users_views.xml',
        'views/sales_return_form_view.xml',
        'views/score_card_detail_view.xml',
        'views/return_code.xml',
        ],
    'assets': {
        'web.assets_backend': [
            'kg_ultracare_sale/static/src/xml/activity_mark_done_popover_content.xml',
        ],
    },

}
