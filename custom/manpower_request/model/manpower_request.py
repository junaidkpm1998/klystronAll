from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ManpowerRequest(models.Model):
    _name = 'manpower.request'
    _rec_name = 'reference_no'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    reference_no = fields.Char(string='Order Reference', required=True,
                               readonly=True, default=lambda self: _('New'))
    department_id = fields.Many2one('hr.department', string="Department", required=True)
    requested_by_id = fields.Many2one('res.users', default=lambda self: self.env.user, readonly=True, )
    vacancy = fields.Integer(string='Total Vacancy', readonly=True)
    approved_cancelled = fields.Char(string='Approved/Cancelled by')
    vacancies_ids = fields.One2many('vacancies', 'vacancy_id')
    state = fields.Selection([('draft', 'Draft'), ('approve', 'Approved'), ('reject', 'Rejected')],
                             readonly=True, copy=False, tracking=True, default='draft')

    @api.onchange('vacancies_ids')
    def onchange_vacancies_ids(self):
        """calculating the count of total vacancies and return into the vacancy field"""
        self.vacancy = sum(self.vacancies_ids.mapped('vacancies'))

    @api.model
    def create(self, vals):
        """generating sequence number"""
        if vals.get('reference_no', _('New')) == _('New'):
            vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                'manpower.request') or _('New')
        res = super(ManpowerRequest, self).create(vals)
        return res

    def action_approve(self):
        """changing the state into 'approved' """
        self.write({'state': 'approve'})

    def action_reject(self):
        """changing the state into 'rejected' """

        self.write({'state': 'reject'})


class Vacancies(models.Model):
    _name = 'vacancies'

    vacancy_id = fields.Many2one('manpower.request', ondelete='cascade')
    job_id = fields.Many2one('hr.job', string="Job", required=True)
    grade_id = fields.Many2one('grades')
    vacancies = fields.Integer(string='Vacancies', default=1)
    salary = fields.Integer(string="Proposed Salary")
    total = fields.Integer(string="Total")
    salary_splitup_ids = fields.One2many('salary.splitup', 'salary_splitup_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, required=True)

    @api.onchange('vacancies')
    def onchange_vacancies(self):
        """generating a user error if the vacancy zero or less"""
        if self.vacancies <= 0:
            raise UserError(_("Vacancy cannot be Zero"))

    @api.onchange('salary_splitup_ids')
    def _total_salary(self):
        """calculating the total amount of salary rules and returns to the salary field"""
        self.salary = sum(self.salary_splitup_ids.mapped('amount'))


class SalarySplitup(models.Model):
    _name = 'salary.splitup'

    salary_splitup_id = fields.Many2one('vacancies', ondelete='cascade')
    salary_rule_id = fields.Many2one('hr.salary.rule', string="Rule", required=True)
    amount = fields.Integer(string="Amount")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, required=True)
