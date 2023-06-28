# -*- coding: utf-8 -*-
{
    'name': "kg_ultracare_contacts",

    "summary": "Employee,Contacts modules",
    "version": "16.0.1.0.0",
    'category': 'Employee/Contacts',
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'contacts', 'contacts_enterprise', 'project', 'hr_attendance', 'stock', 'mrp',
                'purchase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/record_rule.xml',
    ],
}
