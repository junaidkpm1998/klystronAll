# -*- coding: utf-8 -*-
from odoo import models, fields


class HrAttendence(models.Model):
    _inherit = 'hr.attendance'

    state = fields.Selection([('not_validate', 'Not Validate'), ('validate', 'Validate')], string='State',
                             default='not_validate', readonly=True)

    def checkout_notification(self):
        """checkout reminder notification"""
        for i in self.search([('check_out', '=', False)]):
            email_values = {
                'email_to': i.employee_id.work_email,
                'email_from': self.env.user.partner_id.email,
                'author_id': self.env.user.partner_id.id,
            }
            mail_template = self.env.ref('kg_hrms_updates.attendance_checkout_mail_template')
            mail_template.sudo().send_mail(i.id, force_send=True, email_values=email_values)

    def btn_validate(self):
        """validate"""
        for i in self:
            i.state = 'validate'
