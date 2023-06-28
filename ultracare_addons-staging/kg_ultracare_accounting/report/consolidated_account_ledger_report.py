import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError


class ConsolidatedAccountLedgerReport(models.AbstractModel):
    _name = 'report.kg_ultracare_accounting.consolidated_ac_ledger_template'
    _description = 'Consolidated Account Ledger Report'


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
        total_debit = 0
        total_credit = 0
        total_balance = 0
        total_opening_balance = 0

        account_id = self.env['account.account'].search([])
        for acc in account_id:
            account_list = {
                'type': 'journal',
                'journal_code': str(acc.code).upper(),
                'journal_name': str(acc.name).upper()
            }
            account_move_line_id = self.env['account.move.line'].search(
                [('date', '>=', date_from), ('date', '<=', date_end), ('move_id.state', '=', 'posted'),
                 ('account_id', '=', acc.id)])
            if len(account_move_line_id) > 0:
                data.append(account_list)
            if account_move_line_id:
                for vals in account_move_line_id:
                    opening_balance = vals.with_context({'to_date': date_from}).balance
                    date = vals.date
                    if vals.payment_id.payment_type:
                        doc_type = \
                        dict(vals.payment_id.fields_get(allfields=['payment_type'])['payment_type']['selection'])[
                            vals.payment_id.payment_type]
                    else:
                        doc_type = ''
                    doc_no = vals.payment_id.name
                    ref_no = vals.ref
                    reference = vals.move_id.payment_reference
                    currency = vals.currency_id.name
                    debit = vals.debit
                    credit = vals.credit
                    balance = vals.balance

                    if debit or credit:
                        account_list = {
                            'type': 'data',
                            'opening_balance': opening_balance,
                            'doc_type': doc_type,
                            'doc_no': doc_no,
                            'date': date,
                            'ref_no': ref_no,
                            'reference': reference,
                            'currency': currency,
                            'debit': debit,
                            'credit': credit,
                            'balance': balance,
                        }
                        data.append(account_list)

                    total_opening_balance += opening_balance
                    total_debit += debit
                    total_credit += credit
                    total_balance += balance

            account_list = {
                'type': 'amount',
                'total_opening_balance': total_opening_balance,
                'total_debit': total_debit,
                'total_credit': total_credit,
                'total_balance': total_balance,
            }
            if total_debit or total_credit or total_balance != 0:
                data.append(account_list)

            total_debit = 0
            total_credit = 0
            total_balance = 0
        # if not data:
        #     raise UserError(_('No data in this date range'))
        if data:
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
        else:
            return data

