from ast import literal_eval

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AdvanceLoans(models.Model):
    _name = 'advance.loan'
    _rec_name = 'employee_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_employee(self):
        """return default salary head from res.config.settings"""
        val = self.env['ir.config_parameter'].sudo().get_param('kg_hrms_updates.salary_head_ids')
        if val:
            data = literal_eval(val)
            lst = []
            for i in data:
                lst.append(i)
            return lst

    employee_id = fields.Many2one('hr.employee', string="Employees", required=True)
    salary_head = fields.Many2many('res.users', string="Salary Head", default=_default_employee, readonly=True)
    loan_type = fields.Selection([('advance', 'Advance'), ('odp', 'ODP Loan'), ('mof', 'MOF')],
                                 required=True,
                                 string="Loan Type")
    loan_bank_account = fields.Many2one('res.partner.bank', string="Loan Bank Account")
    loan_amount = fields.Float(string="Loan Amount", required=True)
    approved_loan_amount = fields.Float(string="Approved Loan Amount", required=True)
    flag = fields.Boolean(default=False)
    request_date = fields.Date(string="Requested Date", required=True)
    repayment_months = fields.Integer(string="Repayment Months", required=True)
    repayment_amount = fields.Float(string="Repayment Amount", required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, required=True)
    approved_by = fields.Many2one('res.users', string="Approved By", required=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('hr_approval', 'HR Manager Approval'), ('gm_approval', 'GM-CS Approval'),
         ('approved', 'Approved'), ('reject', 'Rejected')], default='draft')


    def to_request(self):
        self.write({'state': 'hr_approval'})
        val = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'open')])
        if not val:
            raise ValidationError(_('Sorry!.. You have no running contract'))

    def gm_approval(self):
        self.write({'state': 'gm_approval'})

    def to_reject(self):
        self.write({'state': 'reject'})

    def to_approve(self):
        val = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'open')])
        if val:
            if val.probation >= 12:
                self.write({'state': 'approved'})
                body = _('Approved Loan Amount is %s', self.loan_amount)
                self.message_post(body=body)
            else:
                self.flag = True
                self.approved_loan_amount = self.loan_amount / 2
                self.write({'state': 'approved'})
                body = _('Approved Loan Amount is %s', self.approved_loan_amount)
                self.message_post(body=body)

    @api.onchange('approved_by')
    def onchange_approved_by(self):
        if self.approved_by:
            if self.approved_by.name != self.env.user.name:
                raise ValidationError(('Only ' + self.env.user.name + ' can approve'))
