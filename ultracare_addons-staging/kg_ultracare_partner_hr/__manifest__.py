{
    'name': 'KG Ultracare HR',
    'version': '16.0.0.0.0',
    'category': 'Extra Tools',
    'summary': 'KG',
    'sequence': '10',
    'license': 'AGPL-3',
    'author': 'Anal P Joy',
    'maintainer': 'KG',
    'website': 'www.klystronglobal.com',
    'depends': ['base', 'hr', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/partner_inherit_view.xml',
        'views/hr_employee_inherit.xml',

        # 'report/service_report.xml',
        # 'report/service_report_templates.xml',
    ],
    # 'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,

}
