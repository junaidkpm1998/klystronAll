import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError


class BankStatusReport(models.AbstractModel):
    _name = 'report.kg_ultracare_accounting.bank_report_template_id'
    _description = 'Bank Status Report'

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
        sum_ledger_balance = 0
        for acc in account_id:
            account_move_line_id = self.env['account.move.line'].search(
                [('date', '>=', date_from), ('move_id.state', '!=', ['draft', 'cancel']),
                 ('journal_id.type', '=', 'bank'), ('account_id', '=', acc.id)],
                order='account_id asc')
            if len(account_move_line_id) > 0:
                account = account_move_line_id[0].account_id.id
                inr = 0
                ledger_balance = 0
                credit_limit = 0

                while (inr < len(account_move_line_id)):
                    if account_move_line_id[inr].account_id.id == account:
                        ledger_balance += account_move_line_id[inr].debit - account_move_line_id[inr].credit
                        credit_limit += account_move_line_id[inr].move_id.partner_id.credit_limit

                    else:
                        rtn_line = self.env['account.move.line'].search(
                            [('date', '>=', date_from), ('move_id.state', '!=', ['draft', 'cancel']),
                             ('journal_id.type', '=', 'bank'),
                             ('account_id', '=', account)])
                        if ledger_balance:
                            data.append(
                                {
                                    'type': 'data',
                                    'account_code': account_move_line_id[inr].account_id.code,
                                    'account_name': str(account_move_line_id[inr].account_id.name).upper(),
                                    'credit_limit': credit_limit,
                                    'ledger_balance': ledger_balance,
                                })

                            sum_ledger_balance += ledger_balance

                        account = account_move_line_id[inr].account_id.id
                        ledger_balance = 0
                        credit_limit = 0

                        ledger_balance += account_move_line_id[inr].debit - account_move_line_id[inr].credit
                        credit_limit += account_move_line_id[inr].move_id.partner_id.credit_limit

                    inr += 1

                rtn_line = self.env['account.move.line'].search(
                    [('date', '>=', date_from), ('move_id.state', '!=', ['draft', 'cancel']),
                     ('journal_id.type', '=', 'bank'),
                     ('account_id', '=', account_move_line_id[inr - 1].account_id.id),
                     ])
                if ledger_balance:
                    data.append(
                        {
                            'type': 'data',
                            'account_code': account_move_line_id[inr - 1].account_id.code,
                            'account_name': str(account_move_line_id[inr - 1].account_id.name).upper(),
                            'credit_limit': credit_limit,
                            'ledger_balance': ledger_balance,
                        })

                    sum_ledger_balance += ledger_balance

            if sum_ledger_balance != 0:
                data.append({
                    'type': 'amount',
                    'sum_ledger_balance': sum_ledger_balance,
                })
            sum_ledger_balance = 0

        # if not data:
        #     raise ValidationError(_('No data in this date range'))

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
