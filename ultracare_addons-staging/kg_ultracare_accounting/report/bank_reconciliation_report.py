import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError


class BankReconciliationReport(models.AbstractModel):
    _name = 'report.kg_ultracare_accounting.bank_reconciliation_template'
    _description = 'Bank Reconciliation Report'

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
        total_debit = 0
        total_credit = 0
        total_balance = 0
        account_id = self.env['account.account'].search([])
        for acc in account_id:
            account_list = {
                'type': 'account',
                'account_code': str(acc.code).upper(),
                'account_name': str(acc.name).upper()
            }
            account_move_line_id = self.env['account.move.line'].search(
                [('date', '>=', date_from), ('move_id.state', '=', 'posted'),
                 ('journal_id.type', '=', 'bank'), ('account_id', '=', acc.id)])
            if len(account_move_line_id) > 0:
                data.append(account_list)
            if account_move_line_id:
                for vals in account_move_line_id:
                    type = str(vals.journal_id.type).upper()
                    doc_no = vals.payment_id.name
                    cheque_no = vals.move_id.name
                    cheque_date = vals.move_id.date
                    narration = vals.payment_id.narration
                    credit = 0
                    debit = 0
                    if vals.payment_id.payment_type == 'outbound':
                        credit = vals.move_id.line_ids[0].credit
                        debit = vals.move_id.line_ids[0].debit
                    if vals.payment_id.payment_type == 'inbound':
                        credit = vals.move_id.line_ids[0].credit
                        debit = vals.move_id.line_ids[0].debit
                    balance = debit - credit

                    account_list = {
                        'type': 'data',
                        'doc_type': type,
                        'doc_no': doc_no,
                        'cheque_no': cheque_no,
                        'cheque_date': cheque_date,
                        'narration': narration,
                        'credit': credit,
                        'debit': debit,
                        'balance': balance,
                    }
                    data.append(account_list)

                    total_debit += debit
                    total_credit += credit
                    total_balance += balance

            account_list = {
                'type': 'amount',
                'total_debit': total_debit,
                'total_credit': total_credit,
                'total_balance': total_balance
            }
            if total_debit or total_credit or total_balance != 0:
                data.append(account_list)
            total_debit = 0
            total_credit = 0
            total_balance = 0

        return {
            'doc_ids': self.ids,
            'datas': data,
            'from_date': date_from,
            'doc_model': model,
            'currency_id': currency_id.name,
            'company_id': browsed_company.name,
            'company_details': browsed_company.company_details,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
        }
