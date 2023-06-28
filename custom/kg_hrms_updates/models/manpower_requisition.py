from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError
import re


class ManpowerRequisition(models.Model):
    _name = "manpower.requisition"
    _rec_name = 'partner_name'

    name = fields.Char(string="Subject", required=True)
    partner_name = fields.Char(string="Applicant Name")
    email_from = fields.Char(string="Email")
    email_cc = fields.Char(string="Email CC")
    partner_phone = fields.Char(string="Phone")
    partner_mobile = fields.Char(string="Mobile")
    partner_mobile = fields.Char(string="Mobile")
    type_id = fields.Many2one('hr.recruitment.degree', string="Degree")
    linkedin_profile = fields.Char(string='Linkedin Profile')
    job_id = fields.Many2one('hr.job', string="Applied Job")
    department_id = fields.Many2one('hr.department', string="Department")
    company_id = fields.Many2one('res.company', string="Company")

    categ_ids = fields.Many2many('hr.applicant.category', 'recruiter_categ_ids_related', string="Tags")
    interviewer_ids = fields.Many2many('res.users', 'recruiter_interviewer_ids_related', string="Interviewers")
    user_id = fields.Many2one('res.users', string="Recruiter")
    source_id = fields.Many2one('utm.source', string="Source")
    medium_id = fields.Many2one('utm.medium', string="Medium")

    salary_expected = fields.Float(string="Expected Salary")
    salary_proposed = fields.Float(string="Proposed Salary")
    availability = fields.Date(string="Availability")
    description = fields.Text()
    state = fields.Selection(
        [('draft', 'Draft'), ('gm_approval', 'G M Approval'), ('hr', 'HR Manager'),
         ('gmcs', 'GMCS Approval'), ('ceo', 'CEO Approval'), ('approved', 'Approved'), ('reject', 'Rejected')],
        default='draft')
    hired_count = fields.Integer(compute='hired_employee')
    employee_button_flag = fields.Boolean(default=False)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, required=True)

    def manpower_requisition(self):
        """change state to gm_approval"""
        self.write({'state': 'gm_approval'})

    def manpower_requisition_reject(self):
        """change state to reject"""
        self.write({'state': 'reject'})

    def manpower_requisition_approve(self):

        """change state into hr approval. only department manager related user can approve.
        else a walidation error will rise"""
        # if self.department_id.manager_id.name == self.env.user.name:
        if self.department_id.manager_id.user_id == self.env.user:
            self.write({'state': 'hr'})
        else:
            if self.department_id.manager_id.user_id:
                raise UserError(_('Only ' + self.department_id.manager_id.user_id.name + ' Can Approve'))
            else:
                raise UserError(_(' Only Department Manager Related User Can Approve'))

    def manpower_requisition_hr_approve(self):
        """when expected salary is greater than payscale total amount,then state changes to GMCS approval,
        otherwise changes to approved state"""
        if self.salary_expected <= sum(self.job_id.pas_scale_ids.mapped('amount')):
            self.write({'state': 'approved'})
        else:
            self.write({'state': 'gmcs'})

    def manpower_requisition_gmcs_approve(self):
        """change state to ceo"""
        self.write({'state': 'ceo'})

    def manpower_requisition_ceo_approve(self):
        """change state to ceo"""
        self.write({'state': 'approved'})

    def hire_employee(self):
        """when applicant get hired, creating record in hr employee"""
        self.employee_button_flag = True
        self.env['hr.applicant'].create({
            'name': self.name,
            'partner_name': self.partner_name,
            'email_from': self.email_from,
            'email_cc': self.email_cc,
            'partner_phone': self.partner_phone,
            'partner_mobile': self.partner_mobile,
            'type_id': self.type_id.id,
            'linkedin_profile': self.linkedin_profile,
            'job_id': self.job_id.id,
            'department_id': self.department_id.id,
            'company_id': self.company_id.id,
            'categ_ids': self.categ_ids,
            'interviewer_ids': self.interviewer_ids,
            'user_id': self.user_id.id,
            'source_id': self.source_id.id,
            'salary_expected': self.salary_expected,
            'salary_proposed': self.salary_proposed,
            'availability': self.availability,
            'description': self.description,
            'manpower_requisition_id': self.id
        })

    def employee_smart_button(self):
        """smart button to view hired employee"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Employee Records',
            'view_mode': 'tree,form',
            'res_model': 'hr.applicant',
            'domain': [('manpower_requisition_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def hired_employee(self):
        """compute function to calculate count of employee in smart button"""
        for record in self:
            record.hired_count = self.env['hr.applicant'].search_count(
                [('manpower_requisition_id', '=', self.id)])

    @api.onchange('email_from', 'email_cc')
    def onchange_private_email(self):
        """validation error for email which is in invalid format"""
        pat = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        email_from = self.email_from
        email_cc = self.email_cc
        if email_from and not re.match(pat, email_from):
            print("inValid Email")
            raise ValidationError("Email from format is  invalid ")
        elif email_cc and not re.match(pat, email_cc):
            print("inValid Email")
            raise ValidationError("Email cc format is  invalid ")
