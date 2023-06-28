from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LeaveSalaryForm(models.Model):
    _name = 'leave.salary.form'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char('Name', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    department_id = fields.Many2one('hr.department', string="Department",
                                    related="employee_id.department_id")
    job_id = fields.Many2one('hr.job', string="Job", related="employee_id.job_id")
    manager_id = fields.Many2one('res.users', string="Manager",
                                 related="employee_id.parent_id.user_id", store=True)
    contract_id = fields.Many2one('hr.contract', string="Contract",
                                  related="employee_id.contract_id")
    state = fields.Selection([('draft', 'Draft'),
                              ('f_approve', 'Waiting'),
                              ('approved', 'Approved'),
                              ('refused', 'Refused')], string="state",
                             default="draft")
    current_user_boolean = fields.Boolean()
    amount = fields.Float("Basic Salary", readonly=True)
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    is_submit = fields.Boolean('Submit')

    salary_structure_type = fields.Many2one('hr.payroll.structure.type', string="Salary Structure Type")
    salary_structure = fields.Many2one('hr.payroll.structure', string="Salary Structure")
    payslip_paid = fields.Boolean(string='Paid In Payslip')

    @api.constrains('employee_id')
    def annual_leave_salary(self):
        for rec in self:
            search_form = self.env['leave.salary.form'].search(
                [('employee_id', '=', rec.employee_id.id), ('state', '=', 'approved')])
            for i in search_form:
                if rec.start_date.year == i.start_date.year:
                    raise ValidationError(_("Sorry you already get the leave salary"))

    @api.model
    def create(self, values):
        seq = self.env['ir.sequence'].next_by_code('leave.salary.form') or '/'
        values['name'] = seq
        return super(LeaveSalaryForm, self.sudo()).create(values)

    @api.onchange('employee_id')
    def _get_defaults(self):
        for sheet in self:
            if sheet.employee_id:
                sheet.update({
                    'department_id': sheet.employee_id.department_id.id,
                    'job_id': sheet.employee_id.job_id.id,
                    'manager_id': sheet.sudo().employee_id.parent_id.user_id.id,
                    'amount': sheet.employee_id.contract_id.basic_salary,
                    'salary_structure_type': sheet.employee_id.contract_id.structure_type_id.id,
                    'salary_structure': sheet.employee_id.contract_id.structure_type_id.leave_structure_id.id,
                })

    def submit_to_f(self):
        self.state = 'f_approve'
        self.is_submit = True

    def approve(self):
        self.state = 'approved'

    def reject(self):
        self.state = 'refused'


class KGStuructureType(models.Model):
    _inherit = "hr.payroll.structure.type"

    leave_structure_id = fields.Many2one('hr.payroll.structure', string="Salary Structure")
