{
    'name': 'KG HRMS',
    'version': '16.0.1.0.0',

    'depends': [
        'hr_payroll'
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/report.xml',
        'report/payroll_comparison_report.xml',
        'report/payroll_comparison_wizard.xml',
        'views/division_master_views.xml',
        'views/hr_job_views.xml',
        'views/hr_employee_views.xml'
    ],
    'installable': True,
    'application': True
}
