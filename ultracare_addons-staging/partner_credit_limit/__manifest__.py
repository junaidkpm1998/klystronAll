# See LICENSE file for full copyright and licensing details.

{
    'name': 'Partner Credit Limit',
    'version': '16.0.1.0.0',
    'category': 'Partner',
    'license': 'AGPL-3',
    'author': 'Tiny, Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://www.serpentcs.com',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'summary': 'Set credit limit warning',
    'depends': [
        'sale_management', 'sale', 'event_sale', 'base', 'account', 'account_accountant', 'mail'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'data/template.xml',
        'data/activity_data.xml',
        'views/partner_view.xml',
        'views/sale_order.xml',
        'wizard/credit_exceed_warning.xml',
    ],
    'installable': True,
    'auto_install': False,
}
