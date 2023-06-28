# -*- coding: utf-8 -*-
{
    'name': "kg_ultracare_hrms",

    "summary": "Employee,Payroll,Payslip modules",
    "version": "16.0.1.0.0",
    'category': 'Employee/Payroll/Payslip',
    'author': "Klystron Global",
    'maintainer': "SHARMI SV",
    "license": "OPL-1",
    'website': 'https://www.klystronglobal.com',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_attendance', 'hr_holidays', 'hr_payroll', 'kg_ultracare_leave_recalculation',
                'hr_holidays_gantt', 'mrp', 'ohrms_overtime', 'l10n_ae_hr_payroll', 'resource','project_enterprise','project','event'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'security/record_rules.xml',

        'data/kg_data.xml',
        'data/payslip_data.xml',

        'report/kg_payslip_report.xml',

        'wizard/kg_payslip_wizard.xml',

        'views/views.xml',
        'views/templates.xml',
        'views/hr_employee_views.xml',
        'views/hr_holiday_views.xml',
        'views/hr_attendance_views.xml',
        'views/leave_salary_form_views.xml',
        'views/hr_leave_report_calendar_views.xml',
        'views/shift_master_view.xml',
        'views/resource_view.xml',
        'views/project_task_views.xml',
        'views/event_event_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
