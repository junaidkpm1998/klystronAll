# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2021-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Ijaz Ahammed (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
{
    'name': 'Open HRMS Overtime',
    'version': '16.0.1.0.0',
    'summary': 'Manage Employee Overtime',
    'description': """
        Helps you to manage Employee Overtime.
        """,
    'category': 'Generic Modules/Human Resources',
    'author': "Cybrosys Techno Solutions,Open HRMS",
    'live_test_url': 'https://youtu.be/lOQCTCxrUKs',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.openhrms.com",
    "license": "AGPL-3",
    'depends': [
        'hr', 'hr_contract', 'hr_attendance', 'hr_holidays', 'project','hr_payroll','account','mail'],
    'external_dependencies': {
        'python': ['pandas'],
    },
    'data': [
        'data/hr_payslip_data.xml',
        'data/sequence.xml',
        'views/overtime_request_view.xml',
        'views/overtime_type.xml',
        'views/hr_contract.xml',
        'views/hr_overtime_summary_views.xml',
        'security/ir.model.access.csv',
    ],
    'demo': ['data/hr_payslip_data.xml'],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
