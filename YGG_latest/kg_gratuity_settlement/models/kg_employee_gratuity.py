from dateutil.relativedelta import relativedelta

from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError


class KGEmployeeGratuity(models.Model):
    _name = "kg.employee.gratuity"
    _description = "Employee Gratuity"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', required=True, copy=False,
                       readonly=True,
                       default=lambda self: _('New'))

    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  required=True, help="Employee")

    employee_joining_date = fields.Date(string='Joining Date',
                                        help="Employee joining date")

    employee_wage_amount = fields.Float(string='Wage',
                                        readonly=True,
                                        help="Employee's Wage salary.")

    contract_id = fields.Many2one('hr.contract', string="Contract")

    gratuity_country = fields.Selection([('ksa', 'Saudi Arabia'), ('qatar', 'Qatar'), ('kuwait', 'Kuwait')], default='ksa',
                                     string="Gratuity Country")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('cancel', 'Cancelled')],
        default='draft', tracking=True)

    last_working_date = fields.Date(string="Last Working Date")

    total_working_years = fields.Float(string='Total Years Worked', readonly=True, store=True,
                                       help="Total working years")

    total_working_days = fields.Float(string='Total Days Worked', readonly=True, store=True,
                                      help="Total working days")

    employee_gratuity_years = fields.Float(string='Gratuity Calculation Years',
                                           readonly=True, store=True, help="Employee gratuity years")

    employee_gratuity_days = fields.Float(string='Gratuity Calculation Days',
                                          readonly=True, store=True, help="Employee gratuity days")

    employee_gratuity_amount = fields.Float(string='Gratuity Payment', readonly=True, store=True,
                                            help="Gratuity amount for the employee")
    hr_gratuity_credit_account = fields.Many2one('account.account', help="Gratuity credit account")

    hr_gratuity_debit_account = fields.Many2one('account.account', help="Gratuity debit account")

    hr_gratuity_journal = fields.Many2one('account.journal', help="Gratuity journal")

    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env.company, help="Company")

    currency_id = fields.Many2one(related="company_id.currency_id",
                                  string="Currency", readonly=True, help="Currency")

    one_day_basic_salary = fields.Float(string="One Day Basic Salary")

    employee_basic_salary = fields.Float(string='Basic Salary',
                                         readonly=True,
                                         help="Employee's basic salary.")

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('kg.gratuity.seq')
        return super(KGEmployeeGratuity, self).create(vals)

    @api.onchange('employee_id')
    def _get_employee_del(self):
        for rec in self:
            if rec.employee_id:
                employee_id = self.env['kg.employee.gratuity'].search(
                    [('employee_id', '=', rec.employee_id.id), ('state', 'not in', ['draft', 'cancel'])])
                if employee_id:
                    raise ValidationError(
                        _('There is a gratuity settlement in confirmed or approved state for this employee'))

                contract_id = self.env['hr.contract'].search(
                    [('employee_id', '=', self.employee_id.id), ('state', '=', 'open')], limit=1)
                rec.contract_id = contract_id.id

                rec.employee_joining_date = min(
                    rec.employee_id.contract_id.mapped('date_start')) if rec.employee_id.contract_id else False

                rec.employee_wage_amount = rec.contract_id.wage
                rec.employee_basic_salary = rec.contract_id.basic_salary

    @api.onchange('employee_joining_date', 'last_working_date')
    def _get_working_years_days(self):
        for rec in self:
            if rec.employee_joining_date and rec.last_working_date:
                delta = rec.last_working_date - rec.employee_joining_date
                rec.total_working_days = delta.days
                rec.total_working_years = rec.total_working_days / 365

                after_one_year_date = rec.employee_joining_date + relativedelta(years=1)
                gratuity_date = rec.last_working_date - after_one_year_date
                rec.employee_gratuity_days = gratuity_date.days
                rec.employee_gratuity_years = rec.employee_gratuity_days / 365

    @api.onchange('total_working_years', 'employee_joining_date', 'last_working_date','gratuity_country')
    def _get_gratuity_value(self):
        for rec in self:
            if rec.total_working_years:
                if rec.gratuity_country == 'ksa':
                    if round(rec.total_working_years) == 2 and rec.last_working_date == rec.contract_id.date_end:
                        rec.employee_gratuity_amount = (rec.employee_wage_amount / 2) * 2
                    elif 2 <= rec.total_working_years < 5:
                        rec.employee_gratuity_amount = round(
                            (rec.employee_wage_amount / 2) * rec.total_working_years * (1 / 3))
                    elif 5 <= rec.total_working_years < 10:
                        two_to_five = (rec.employee_wage_amount / 2) * 5 * (2 / 3)
                        six_to_ten = rec.employee_wage_amount * (rec.total_working_years - 5) * (2 / 3)
                        rec.employee_gratuity_amount = round(two_to_five + six_to_ten)
                    else:
                        two_to_five = (rec.employee_wage_amount / 2) * 5
                        six_to_end = rec.employee_wage_amount * (rec.total_working_years - 5)
                        rec.employee_gratuity_amount = round(two_to_five + six_to_end)

                if rec.gratuity_country == 'kuwait':
                    if 3 <= rec.total_working_years < 5:
                        rec.employee_gratuity_amount = round(
                            (rec.employee_basic_salary / 2) * rec.total_working_years * (1 / 2))
                    elif 5 <= rec.total_working_years < 10:
                        three_to_five = (rec.employee_basic_salary / 2) * 5 * (2 / 3)
                        six_to_ten = rec.employee_basic_salary * (rec.total_working_years - 5) * (2 / 3)
                        rec.employee_gratuity_amount = round(three_to_five + six_to_ten)
                    else:
                        three_to_five = (rec.employee_basic_salary / 2) * 5
                        six_to_end = rec.employee_basic_salary * (rec.total_working_years - 5)
                        rec.employee_gratuity_amount = round(three_to_five + six_to_end)

                if rec.gratuity_country == 'qatar':
                    if 1 <= rec.total_working_years < 5:
                        rec.employee_gratuity_amount = round(
                            (rec.employee_basic_salary / 30) * 21 * rec.total_working_years)
                    elif 1 <= rec.total_working_years < 10:
                        rec.employee_gratuity_amount = round(
                            (rec.employee_basic_salary / 30) * 28 * rec.total_working_years)
                    else:
                        rec.employee_gratuity_amount = round(
                            (rec.employee_basic_salary / 30) * 35 * rec.total_working_years)

    @api.constrains('employee_joining_date', 'last_working_date', 'total_working_years')
    def check_constrains(self):
        for rec in self:
            if rec.employee_joining_date and rec.last_working_date:
                if rec.employee_joining_date > rec.last_working_date:
                    raise ValidationError(_('Employee Joining Date must be less than Last Working Date'))
            if rec.total_working_years:
                if rec.gratuity_country == 'ksa':
                    if rec.total_working_years < 2:
                        raise UserError(_('Employee Working Period Must be Greater Than 2 Year'))
                if rec.gratuity_country == 'kuwait':
                    if rec.total_working_years < 3:
                        raise UserError(_('Employee Working Period Must be Greater Than 3 Year'))
                if rec.gratuity_country == 'qatar':
                    if rec.total_working_years < 1:
                        raise UserError(_('Employee Working Period Must be Greater Than 1 Year'))

    def submit_request(self):
        self.write({'state': 'submit'})

    def cancel_request(self):
        self.write({'state': 'cancel'})

    def set_to_draft(self):
        self.write({'state': 'draft'})

    def approved_request(self):
        self.write({'state': 'approve'})

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel'):
                raise UserError(
                    'You cannot delete a gratuity which is not in draft or cancelled state')
        return super(KGEmployeeGratuity, self).unlink()
