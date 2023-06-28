import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError


class BalanceSheetScheduleReport(models.AbstractModel):
    _name = 'report.kg_ultracare_accounting.balance_sheet_sche_template'
    _description = 'Balance Sheet Schedule Report'

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

        account_id = self.env['account.account'].search([])
        data_list = []
        sum_debit = 0
        sum_credit = 0
        for acc in account_id:
            account_move_line_id = self.env['account.move.line'].search(
                [('date', '>=', date_from), ('date', '<=', date_end),
                 ('move_id.state', '=', 'posted'), ('account_id', '=', acc.id)],order='account_id asc')

            account_name = str(acc.name).upper()
            account_list = {'type': 'account',
                             'account_name': account_name,
                             }
            if len(account_move_line_id) > 0:
                data_list.append(account_list)

            if len(account_move_line_id) > 0:
                account = account_move_line_id[0].account_id.id
                inr = 0
                debit = 0
                credit = 0

                while (inr < len(account_move_line_id)):
                    if account_move_line_id[inr].account_id.id == account:
                        debit += account_move_line_id[inr].debit
                        credit += account_move_line_id[inr].credit

                    else:
                        rtn_line = self.env['account.move.line'].search(
                            [('date', '>=', date_from), ('date', '<=', date_end), ('move_id.state', '=', 'posted'),
                             ('account_id', '=', account)])
                        data_list.append(
                            {
                                'type': 'data',
                                'account_code': account_move_line_id[inr].account_id.code,
                                'account_name': account_move_line_id[inr].account_id.name,
                                'debit': debit,
                                'credit': credit,
                            })

                        sum_debit += debit
                        sum_credit += credit

                        account = account_move_line_id[inr].account_id.id
                        credit = 0
                        debit = 0

                        debit += account_move_line_id[inr].debit
                        credit += account_move_line_id[inr].credit
                    inr += 1

                rtn_line = self.env['account.move.line'].search(
                    [('date', '>=', date_from), ('date', '<=', date_end), ('move_id.state', '=', 'posted'),
                     ('account_id', '=', account_move_line_id[inr - 1].account_id.id),
                     ])

                data_list.append(
                    {
                        'type': 'data',
                        'account_code': account_move_line_id[inr - 1].account_id.code,
                        'account_name': account_move_line_id[inr - 1].account_id.name,
                        'debit': debit,
                        'credit': credit,
                    })
                sum_debit += debit
                sum_credit += credit
            if sum_debit or sum_credit != 0:
                data_list.append({
                    'type': 'amount',
                    'sum_debit': sum_debit,
                    'sum_credit': sum_credit,
                })
            sum_debit = 0
            sum_credit = 0

        # if not data_list:
        #     raise ValidationError(_('No data in this date range'))

        return {
            'doc_ids': self.ids,
            'datas': data_list,
            'from_date': date_from,
            'to_date': date_end,
            'doc_model': model,
            'currency_id': currency_id.name,
            'company_id': browsed_company.name,
        }
