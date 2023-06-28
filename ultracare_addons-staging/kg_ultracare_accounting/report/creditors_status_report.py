import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError


class CreditorsStatusReport(models.AbstractModel):
    _name = 'report.kg_ultracare_accounting.creditors_report_template_id'
    _description = 'Creditors Status Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        company_id = data['form'].get('company_id')
        date_end = data['form'].get('date_to', time.strftime('%Y-%m-%d'))
        browsed_currency_id = data['form'].get('currency_id')
        currency_id = self.env['res.currency'].browse(browsed_currency_id[0])
        browsed_company = self.env['res.company'].browse(company_id[0])

        data = []
        account_move_id = self.env['account.move'].search(
            [('date', '<=', date_end), ('state', '!=', ['draft', 'cancel']),('move_type','=','in_invoice')])
        total_customer_credit_amount = sum(account_move_id.mapped('amount_total_signed'))
        for vals in account_move_id:
            customer_code = vals.partner_id.customer_code
            customer_name = vals.partner_id.name
            credit_limit = vals.partner_id.credit_limit
            ledger_balance = vals.amount_total_signed
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
            'total_due_amount': "{0:.2f}".format(total_customer_credit_amount),
            'doc_model': model,
            'currency_id': currency_id,
            'company_id': browsed_company.name,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
            'to_date': date_end
        }
