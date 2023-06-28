import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError


class DebtorsStatusReport(models.AbstractModel):
    _name = 'report.kg_ultracare_accounting.debtors_report_template_id'
    _description = 'Debtors Status Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        company_id = data['form'].get('company_id')
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
        browsed_currency_id = data['form'].get('currency_id')
        currency_id = self.env['res.currency'].browse(browsed_currency_id[0])
        browsed_company = self.env['res.company'].browse(company_id[0])

        data = []
        partner_search = self.env['res.partner'].search([])
        total_customer_due_amount = sum(partner_search.mapped('total_due'))
        for vals in partner_search:
            customer_code = vals.with_context({'to_date': date_from}).customer_code
            customer_name = vals.with_context({'to_date': date_from}).name
            credit_limit = vals.with_context({'to_date': date_from}).credit_limit
            ledger_balance = vals.with_context({'to_date': date_from}).total_due
            if ledger_balance:
                customer = {
                    'customer_code': customer_code,
                    'customer_name': customer_name,
                    'credit_limit': credit_limit,
                    'ledger_balance': ledger_balance,
                }
                data.append(customer)

        # if not data:
        #     raise ValidationError(_('No data in this date range'))

        return {
            'doc_ids': self.ids,
            'datas': data,
            'total_due_amount': "{0:.2f}".format(total_customer_due_amount),
            'doc_model': model,
            'currency_id': currency_id,
            'company_id': browsed_company.name,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
            'to_date': date_from
        }
