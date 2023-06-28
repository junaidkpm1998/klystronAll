# -*- coding: utf-8 -*-
from datetime import date

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError


class HrSalaryCertificate(models.Model):
    _name = 'hr.salary.certificate'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_user(self):
        """storing the current user to user_ids fields"""
        return self.env.user

    name = fields.Char(string='Document Number', readonly=True, default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    employee_type = fields.Many2one('hr.contract.type', required=True)
    requested_date = fields.Date(required=True, default=date.today())
    last_working_date = fields.Date(required=True)
    type = fields.Selection([('direct', 'Direct'), ('indirect', 'Indirect')], required=True)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed')], default='draft', string="Status")
    employee_print_count = fields.Integer('Employee Print Count', default=0)
    user_ids = fields.Many2many('res.users', default=_default_user)

    @api.model
    def create(self, vals):
        """autogenerate unique document number"""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'salary.certificate.sequence') or False
            res = super(HrSalaryCertificate, self).create(vals)
            return res

    def create_request(self):
        """confirmed button"""
        self.write({
            'state': 'confirm'
        })

    def print_salary(self):
        """Print the salary certificate"""
        data = {
            'form': self.read()[0],
        }
        group_admin = self.env.ref('hr.group_hr_manager')
        admin = group_admin.users
        if self.user_ids.id in admin.ids:
            print('admin')
            return self.env.ref('kg_hrms_updates.report_salary_certificate').report_action(self, data=data)

        else:
            if self.employee_print_count == 0:
                self.employee_print_count += 1
                return self.env.ref('kg_hrms_updates.report_salary_certificate').report_action(self, data=data)
            else:
                raise ValidationError("Employee can print this salary certificate only once!!!!!!!!")
