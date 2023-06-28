from odoo import models, fields, api, _
import datetime
from datetime import timedelta
from datetime import date
import calendar
from dateutil.relativedelta import relativedelta

from odoo.exceptions import ValidationError


class KGPayrollCompaWizard(models.TransientModel):
    _name = 'kg.payroll.comparison.wizard'
    description = "Payroll Comparison Wizard"

    @api.model
    def year_selection(self):
        year = 2021  # replace 2021 with your a start year
        year_list = []
        while year != 3051:  # replace 3051 with your end year
            year_list.append((str(year), str(year)))
            year += 1
        return year_list

    previous_start_date = fields.Date(string="Previous Start Date")
    previous_end_date = fields.Date(string="Previous End Date")
    current_start_date = fields.Date(string="Current Start Date")
    current_end_date = fields.Date(string="Current End Date")

    month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December')], string='Month', default=str(date.today().month))

    year = fields.Selection(year_selection, string="Year", default=str(datetime.datetime.now().year))

    employee_id = fields.Many2many('hr.employee', string='Employee')

    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id,
                                 string='Company')

    @api.onchange('year', 'month')
    def _get_dates(self):
        for rec in self:
            if rec.year and rec.month:

                """Get Current End date based on month and year"""
                res = calendar.monthrange(int(rec.year), int(rec.month))
                day = res[1]
                vals = str(rec.year) + '-' + str(rec.month) + '-' + str(day)
                vals_datetime = datetime.datetime.strptime(vals, '%Y-%m-%d')
                rec.current_end_date = vals_datetime.date()

                """Get Current Start date based on month and year"""
                if rec.current_end_date:
                    rec.current_start_date = rec.current_end_date.replace(day=1)

                """Get Previous Start date based on month and year"""
                if rec.current_start_date:
                    dt = rec.current_start_date.replace(day=1)
                    dt = dt - timedelta(days=1)
                    rec.previous_start_date = dt.replace(day=1)

                """Get Previous End date based on month and year"""
                if rec.previous_start_date:
                    rec.previous_end_date = rec.previous_start_date - relativedelta(day=31)

    def print_payroll_com_report(self):
        vals = []

        if not self.employee_id:
            payslip_id = self.env['hr.payslip'].search(
                [('date_from', '>=', self.previous_start_date), ('date_from', '<=', self.current_end_date),
                 ('state', '!=', 'draft')])
            employees = list(set((payslip_id.mapped('employee_id'))))

            for emp in employees:
                emp_payslips = payslip_id.filtered(lambda x: x.employee_id.id == emp.id)
                prev_month_payslip = emp_payslips.filtered(
                    lambda x: x.date_from >= self.previous_start_date and x.date_from <= self.previous_end_date)
                current_month_payslip = emp_payslips.filtered(
                    lambda x: x.date_from >= self.current_start_date and x.date_from <= self.current_end_date)

                lines = {
                    'employee_name': emp.name,
                    'prev_payslip_ref': " , ".join(prev_month_payslip.mapped('number')),
                    'prev_basic_wage': sum(prev_month_payslip.mapped('basic_wage')),
                    'prev_net_wage': sum(prev_month_payslip.mapped('net_wage')),
                    'current_payslip_ref': " , ".join(current_month_payslip.mapped('number')),
                    'current_net_wage': sum(current_month_payslip.mapped('net_wage')),
                    'current_basic_wage': sum(current_month_payslip.mapped('basic_wage')),
                    'currency': self.currency_id.symbol,
                }
                vals.append(lines)

        if self.employee_id:
            for emp_1 in self.employee_id:
                payslip_id = self.env['hr.payslip'].search(
                    [('date_from', '>=', self.previous_start_date), ('date_from', '<=', self.current_end_date),
                     ('state', '!=', 'draft'), ('employee_id', '=', emp_1.id)])
                employees = list(set((payslip_id.mapped('employee_id'))))

                for emp in employees:
                    emp_payslips = payslip_id.filtered(lambda x: x.employee_id.id == emp.id)
                    prev_month_payslip = emp_payslips.filtered(
                        lambda x: x.date_from >= self.previous_start_date and x.date_from <= self.previous_end_date)
                    current_month_payslip = emp_payslips.filtered(
                        lambda x: x.date_from >= self.current_start_date and x.date_from <= self.current_end_date)

                    lines = {
                        'employee_name': emp.name,
                        'prev_payslip_ref': " , ".join(prev_month_payslip.mapped('number')),
                        'prev_basic_wage': sum(prev_month_payslip.mapped('basic_wage')),
                        'prev_net_wage': sum(prev_month_payslip.mapped('net_wage')),
                        'current_payslip_ref': " , ".join(current_month_payslip.mapped('number')),
                        'current_net_wage': sum(current_month_payslip.mapped('net_wage')),
                        'current_basic_wage': sum(current_month_payslip.mapped('basic_wage')),
                        'currency': self.currency_id.symbol,
                    }
                    vals.append(lines)

        if not vals:
            raise ValidationError(_('No data in this date range'))

        data = {
            'form_data': self.read()[0],
            'values': vals,
            'company_name': self.company_id.name,
            'company_zip': self.company_id.zip,
            'company_state': self.company_id.state_id.name,
            'company_country': self.company_id.country_id.name,
            'previous_start_date': self.previous_start_date,
            'previous_end_date': self.previous_end_date,
            'current_start_date': self.current_start_date,
            'current_end_date': self.current_end_date,
        }
        return self.env.ref('kg_hrms_updates.action_payroll_comparison_report').report_action(self, data=data)
