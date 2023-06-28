# -*- coding: utf-8 -*-
from odoo import models, fields


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    promoted_employee_count = fields.Integer('Promoted Employee Count', compute='compute_total_promoted_count')
    employee_transfer = fields.Integer('Employee Transfer', compute='compute_total_transfer_count')
    omani_expat_ratio = fields.Integer('Omani & Expat Ratio', compute='compute_total_omani_count')

    def compute_total_promoted_count(self):
        """calculating the count of promoted employee"""
        count = self.env['hr.employee'].search_count(
            [('department_id', '=', self.id), ('is_promoted', '=', 'True')])
        self.promoted_employee_count = count

    def compute_total_transfer_count(self):
        """calculating the count of transferred employee"""
        count = self.env['hr.employee'].search_count(
            [('department_id', '=', self.id), ('is_transfer', '=', 'True')])
        self.employee_transfer = count

    def compute_total_omani_count(self):
        """calculating the count of employee in a department which has nationality 'oman'"""
        count = self.env['hr.employee'].search_count(
            [('department_id', '=', self.id), ('country_id.name', '=', 'Oman')])
        self.omani_expat_ratio = count
