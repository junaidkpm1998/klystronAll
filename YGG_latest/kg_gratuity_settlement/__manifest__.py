# -*- coding: utf-8 -*-
{
    'name': 'Gratuity Settlement',
    'version': '16.0.1.0.0',
    'summary': """Employee Gratuity Settlement""",
    'author': 'SHARMI SV',
    'company': 'Klystron Global',
    'website': 'https://www.klystronglobal.com',
    'depends': ['base', 'hr_contract', 'hr', 'account', 'hr_work_entry_contract_enterprise'],
    'data': [
        'security/ir.model.access.csv',

        'data/sequence.xml',

        'views/kg_employee_gratuity_views.xml',
        'views/hr_contract_views.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
