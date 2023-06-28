import re

from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('others', 'Others')])
    martial_status = fields.Selection([('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced')])
    nationality_id = fields.Many2one('res.country', string='Nationality', required=True)
    certificate = fields.Image(string='Certifications', required=True)
    experience = fields.Integer(required=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachment', required=True)
    remarks = fields.Text(string='Remarks', required=True)
    manpower_requisition_id = fields.Many2one('manpower.requisition', readonly=True)

    @api.onchange('email_from', 'email_cc')
    def onchange_private_email(self):
        """Validation error for email which is in invalid format"""
        pat = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        email_from = self.email_from
        email_cc = self.email_cc
        if email_from and not re.match(pat, email_from):
            print("inValid Email")
            raise ValidationError("Email from format is  invalid ")
        elif email_cc and not re.match(pat, email_cc):
            print("inValid Email")
            raise ValidationError("Email cc format is  invalid ")

    def create_employee_from_applicant(self):
        """adding the additional fields from hr_applicant to hr_employee"""
        res = super(HrApplicant, self).create_employee_from_applicant()

        if self.partner_id:
            contact_name = self.partner_id.display_name
        else:
            if not self.partner_name:
                raise UserError(_('You must define a Contact Name for this applicant.'))
            new_partner_id = self.env['res.partner'].create({
                'is_company': False,
                'type': 'private',
                'name': self.partner_name,
                'email': self.email_from,
                'phone': self.partner_phone,
                'mobile': self.partner_mobile
            })
            self.partner_id = new_partner_id
        res['context']['default_first_name'] = self.partner_name or contact_name
        res['context']['default_last_name'] = False
        res['context']['default_initials'] = False
        res['context']['default_country_id'] = self.nationality_id.id
        res['context']['default_gender'] = self.gender
        res['context']['default_martial'] = self.martial_status
        res['context']['default_qualification'] = self.experience

        return res
