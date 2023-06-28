import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError


class DetailedExpenseReport(models.AbstractModel):
    _name = 'report.kg_ultracare_accounting.detailed_expense_tem_id'
    _description = 'Detailed Expense Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        company_id = data['form'].get('company_id')
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
        date_end = data['form'].get('date_to', time.strftime('%Y-%m-%d'))
        browsed_currency_id = data['form'].get('currency_id')
        currency_id = self.env['res.currency'].browse(browsed_currency_id[0])
        browsed_company = self.env['res.company'].browse(company_id[0])

        data = []
        hr_expense_id = self.env['hr.expense'].search(
            [('date', '>=', date_from), ('date', '<=', date_end), ('state', '!=', ['draft', 'refused'])])
        for exp in hr_expense_id:
            date = exp.date
            code = exp.account_id.code
            account_name = exp.account_id.name
            description = exp.name
            amount = exp.total_amount_company

            expense_list = {
                'type':'data',
                'date':date,
                'code':code,
                'account_name':account_name,
                'description':description,
                'amount':amount,
            }
            data.append(expense_list)

        return {
            'doc_ids': self.ids,
            'datas': data,
            'from_date': date_from,
            'to_date': date_end,
            'doc_model': model,
            'currency_id': currency_id.name,
            'company_id': browsed_company.name,
            'company_details': browsed_company.company_details,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
        }
