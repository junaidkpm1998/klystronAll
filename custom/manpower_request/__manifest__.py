{
    'name': 'Manpower Request',
    'version': '16.0.1.0.0',
    'category': 'Human Resources',
    'sequence': -1,
    'installable': True,
    'application': True,
    'depends': ['base', 'hr_recruitment'],

    'data': [
        'data/sequence_no.xml',
        'security/ir.model.access.csv',
        'views/manpower_request_view.xml',
        'views/grades_view.xml',
        'views/menu.xml'
    ]
}
