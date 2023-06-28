import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError


class OpeningBalanceReport(models.AbstractModel):
    _name = 'report.kg_ultracare_accounting.opening_balance_report_tem_id'
    _description = 'Opening Balance Report'

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
        account_id = self.env['account.account'].search([])
        for acc in account_id:
            account_list = {
                'type': 'account',
                'account_name': str(acc.name).upper(),
                'account_code': str(acc.code).upper()
            }
            account_move_id = self.env['account.move.line'].search(
                [('date', '<=', date_from), ('move_id.state', '=', 'posted'), ('account_id', '=', acc.id)])
            customer_id = account_move_id.mapped('partner_id')
            if len(account_move_id) > 0 and customer_id:
                data.append(account_list)

            if account_move_id:
                for vals in account_move_id:
                    customer_code = vals.move_id.partner_id.customer_code
                    customer_name = vals.move_id.partner_id.name
                    debit = vals.debit
                    credit = vals.credit
                    if customer_name:
                        account_list = {
                            'type': 'data',
                            'customer_code': customer_code,
                            'customer_name': customer_name,
                            'debit': debit,
                            'credit': credit,
                        }
                        data.append(account_list)

        return {
            'doc_ids': self.ids,
            'datas': data,
            'doc_model': model,
            'currency_id': currency_id,
            'company_id': browsed_company.name,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
            'date_from': date_from
        }
