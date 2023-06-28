{
    'name': 'Partner Ledger Dynamic Report',
    'version': '16.0.1.0.0',
    'category': 'account',
    'sequence': -1,
    'installable': True,
    'application': True,
    'depends': ['base', 'account'],

    'data': [
        'security/ir.model.access.csv',
        'report/pdf_report.xml',
        "wizard/partner_ledger_wizard_view.xml",
        "view/menu.xml"
    ]
}
