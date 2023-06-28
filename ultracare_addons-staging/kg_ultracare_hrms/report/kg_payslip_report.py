import time
from odoo import api, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime


class KGPayslipAnalysisReport(models.AbstractModel):
    _name = 'report.kg_ultracare_hrms.kg_payslip_template_id'
    _description = 'Payslip Analysis Report'

    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        company_id = data['form'].get('company_id')
        year = data['form'].get('year')

        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
        # date_from = datetime.strptime(date_start, '%Y-%m-%d')

        date_end = data['form'].get('date_to', time.strftime('%Y-%m-%d'))
        # date_end = datetime.strptime(end_date, '%Y-%m-%d')

        browsed_currency_id = data['form'].get('currency_id')
        currency_id = self.env['res.currency'].browse(browsed_currency_id[0])
        browsed_company = self.env['res.company'].browse(company_id[0])

        employee_ids = data['form'].get('employee_id')
        data = []

        if employee_ids:
            payslip_id = self.env['hr.payslip'].search(
                [('employee_id', 'in', employee_ids), ('date_from', '>=', date_from), ('state', '!=', 'draft'),
                 ('date_to', '<=', date_end)],order='employee_id asc')
            for pay in payslip_id:
                employee = pay.employee_id.name
                batch = pay.payslip_run_id.name
                number = pay.number
                start_date = pay.date_from
                end_date = pay.date_to
                total_salary = pay.net_wage
                status = pay.state

                payslip_del = {
                    'employee': str(employee).upper(),
                    'batch': batch,
                    'number': number,
                    'start_date': start_date,
                    'end_date': end_date,
                    'total_salary': total_salary,
                    'status': status,
                }
                data.append(payslip_del)

        else:
            payslip_id = self.env['hr.payslip'].search(
                [('date_from', '>=', date_from), ('date_to', '<=', date_end), ('state', '!=', 'draft')],order='employee_id asc')
            for pay in payslip_id:
                employee = pay.employee_id.name
                batch = pay.payslip_run_id.name
                number = pay.number
                start_date = pay.date_from
                end_date = pay.date_to
                total_salary = pay.net_wage
                status = pay.state

                payslip_del = {
                    'employee': str(employee).upper(),
                    'batch': batch,
                    'number': number,
                    'start_date': start_date,
                    'end_date': end_date,
                    'total_salary': total_salary,
                    'status': status,
                }

                data.append(payslip_del)

        return {
            'doc_ids': self.ids,
            'datas': data,
            'doc_model': model,
            'currency_id': currency_id,
            'company_id': browsed_company.name,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
            'from_date': date_from,
            'to_date': date_end
        }
