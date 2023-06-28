{
    'name': 'KG HRMS Updates',
    'version': '16.0.1.0.0',

    'depends': [
        'base', 'hr', 'mail', 'hr_recruitment', 'fleet', 'hr_attendance', 'hr_payroll', 'documents'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/attendence_checkout_email.xml',
        'data/attendence_checkout_email_template.xml',
        'data/sequence.xml',
        'data/hr_salary_certificate_print.xml',
        'data/salary_certificate_template.xml',
        'data/hr_attendance_server_action.xml',

        'report/report.xml',
        'report/payroll_comparison_report.xml',
        'report/payroll_comparison_wizard.xml',

        'views/hr_employee_requests_views.xml',
        'views/hr_employee_vehicle_views.xml',
        'views/hr_applicant_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_department_views.xml',
        'views/hr_salary_certificate_views.xml',
        'views/advance_loans_views.xml',
        'views/res_config_settings_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_job_views.xml',
        'views/interview_form_views.xml',
        'views/manpower_requistion_views.xml',
        'views/menu.xml',
        'views/hr_attendance_views.xml',

    ],
    'installable': True,
    'application': True
}
