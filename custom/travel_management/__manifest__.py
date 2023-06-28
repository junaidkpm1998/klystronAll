{
    'name': 'Travel Management',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'sequence': -1,
    'installable': True,
    'application': True,
    'depends': ['base', 'mail'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/travel_management_action.xml',
        'views/travel_management_service_action.xml',
        'views/vehicle.xml',
        'views/tour_package.xml',
        'views/vehicle_facilities.xml',
        'data/tm_service_types.xml',
        'report/tm_pdf_report.xml',
        'wizard/travel_management_wizard_view.xml',
        'views/travel_management_menu.xml'

    ]
}
