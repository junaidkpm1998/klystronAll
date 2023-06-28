from datetime import date

from odoo import api, fields, models, _
from datetime import date, timedelta, datetime
import calendar


class KGPayslipWizard(models.TransientModel):
    """Payslip Analysis wizard."""

    _name = 'kg.payslip.report.wizard'
    _description = 'Report Wizard'

    @api.model
    def kg_year_selection(self):
        year = 2000  # replace 2000 with your a start year
        year_list = []
        while year != 6000:  # replace 2030 with your end year
            year_list.append((str(year), str(year)))
            year += 1
        return year_list

    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id,
                                 string='Company')
    employee_id = fields.Many2many('hr.employee', String='Employee')
    year = fields.Selection(kg_year_selection, string='Year', default=str(date.today().year))
    salary_month_number = fields.Integer(string='Salary Month', default=date.today().month)
    salary_month = fields.Selection([('01', 'January'),
                                     ('02', 'February'),
                                     ('03', 'March'),
                                     ('04', 'April'),
                                     ('05', 'May'),
                                     ('06', 'June'),
                                     ('07', 'July'),
                                     ('08', 'August'),
                                     ('09', 'September'),
                                     ('10', 'October'),
                                     ('11', 'November'),
                                     ('12', 'December')
                                     ], string="Month of Salary")

    @api.onchange('salary_month_number')
    def _onchange_salary_month(self):
        for rec in self:
            if rec.salary_month_number == 1:
                rec.salary_month = '01'
            if rec.salary_month_number == 2:
                rec.salary_month = '02'
            if rec.salary_month_number == 2:
                rec.salary_month = '02'
            if rec.salary_month_number == 3:
                rec.salary_month = '03'
            if rec.salary_month_number == 4:
                rec.salary_month = '04'
            if rec.salary_month_number == 5:
                rec.salary_month = '05'
            if rec.salary_month_number == 6:
                rec.salary_month = '06'
            if rec.salary_month_number == 7:
                rec.salary_month = '07'
            if rec.salary_month_number == 8:
                rec.salary_month = '08'
            if rec.salary_month_number == 9:
                rec.salary_month = '09'
            if rec.salary_month_number == 10:
                rec.salary_month = '10'
            if rec.salary_month_number == 11:
                rec.salary_month = '11'
            if rec.salary_month_number == 12:
                rec.salary_month = '12'

    @api.onchange('year', 'salary_month')
    def onchange_month(self):
        if self.salary_month == '01':
            self.salary_month_number = 1
        if self.salary_month == '02':
            self.salary_month_number = 2
        if self.salary_month == '03':
            self.salary_month_number = 3
        if self.salary_month == '04':
            self.salary_month_number = 4
        if self.salary_month == '05':
            self.salary_month_number = 5
        if self.salary_month == '06':
            self.salary_month_number = 6
        if self.salary_month == '07':
            self.salary_month_number = 7
        if self.salary_month == '08':
            self.salary_month_number = 8
        if self.salary_month == '09':
            self.salary_month_number = 9
        if self.salary_month == '10':
            self.salary_month_number = 10
        if self.salary_month == '11':
            self.salary_month_number = 11
        if self.salary_month == '12':
            self.salary_month_number = 12
        if self.year:
            month_date = date(int(self.year), int(self.salary_month_number), 1)
            self.date_from = month_date.replace(day=1)
            self.date_to = month_date.replace(day=calendar.monthrange(month_date.year, month_date.month)[1])

    def _export(self, report_type):
        return self._print_report(report_type)

    def kg_payslip_button(self):
        self.ensure_one()
        report_type = "qweb-pdf"
        return self._export(report_type)

    def _print_report(self, data):
        res = {}
        data = {
            'model': 'kg.payslip.report.wizard',
            'form': self.read()[0]
        }
        return self.env.ref('kg_ultracare_hrms.action_kg_payslip_report').with_context(
            landscape=False).report_action(self, data=data)
