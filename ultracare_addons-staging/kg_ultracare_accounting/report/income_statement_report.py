import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError


class IncomeStatementReport(models.AbstractModel):
    _name = 'report.kg_ultracare_accounting.income_statement_report_tem_id'
    _description = 'Income Statement Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        company_id = data['form'].get('company_id')
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
        last_year = data['form'].get('last_year', time.strftime('%Y-%m-%d'))
        browsed_currency_id = data['form'].get('currency_id')
        currency_id = self.env['res.currency'].browse(browsed_currency_id[0])
        browsed_company = self.env['res.company'].browse(company_id[0])

        data = []

        return {
            'doc_ids': self.ids,
            'datas': data,
            'doc_model': model,
            'currency_id': currency_id,
            'company_id': browsed_company.name,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
            'date_from': date_from,
            'last_year': last_year
        }