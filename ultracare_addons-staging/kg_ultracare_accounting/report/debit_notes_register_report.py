import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError


class DebitNotesRegisterReport(models.AbstractModel):
    _name = 'report.kg_ultracare_accounting.debit_not_reg_tem_id'
    _description = 'Debit Notes Register Report'

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

        account_move_id = self.env['account.move'].search(
            [('date', '>=', date_from), ('date', '<=', date_end), ('state', '!=', ['draft', 'cancel']),
             ('move_type', '=', 'in_refund')], order='date asc')
        for vals in account_move_id:
            date = vals.date
            doc_no = vals.name
            reference = vals.ref
            description = vals.line_ids[-1].name
            account_code = vals.line_ids[-1].account_id.code
            account_name = vals.line_ids[1].account_id.name
            debit = vals.line_ids[-1].debit
            credit = vals.line_ids[-1].credit

            debit_notes_list = {
                'type': 'data',
                'date': date,
                'doc_no': doc_no,
                'reference': reference,
                'account_code': account_code,
                'account_name': account_name,
                'description': description,
                'debit': debit,
                'credit': credit,
            }
            data.append(debit_notes_list)

        # values = []
        # account_move_acc_id = self.env['account.move'].search(
        #     [('date', '>=', date_from), ('date', '<=', date_end), ('state', '!=', ['draft', 'cancel']),
        #      ('move_type', '=', 'in_refund')])
        # if len(account_move_acc_id) > 0:
        #     account = account_move_acc_id[0].line_ids[-1].account_id.id
        #     inr = 0
        #     debit = 0
        #     credit = 0
        #     while (inr < len(account_move_acc_id)):
        #         if account_move_acc_id[inr].line_ids[-1].account_id.id == account:
        #             debit += account_move_acc_id[inr].line_ids[-1].debit
        #             credit += account_move_acc_id[inr].line_ids[-1].credit
        #         else:
        #             rtn_line = self.env['account.move'].search(
        #                 [('date', '>=', date_from), ('date', '<=', date_end), ('state', '!=', ['draft', 'cancel']),
        #                  ('move_type', '=', 'in_refund')])
        #             values.append({
        #                 'type': 'value',
        #                 'account_code': account_move_acc_id[inr - 1].line_ids[-1].account_id.code,
        #                 'account_name': account_move_acc_id[inr - 1].line_ids[-1].account_id.name,
        #                 'debit': debit,
        #                 'credit': credit,
        #             })
        #             account = account_move_acc_id[0].line_ids[-1].account_id.id
        #             debit = 0
        #             credit = 0
        #             debit += account_move_acc_id[inr].line_ids[-1].debit
        #             credit += account_move_acc_id[inr].line_ids[-1].credit
        #         inr += 1
        #     rtn_line = self.env['account.move'].search(
        #         [('date', '>=', date_from), ('date', '<=', date_end), ('state', '!=', ['draft', 'cancel']),
        #          ('move_type', '=', 'in_refund'),
        #          ('line_ids.account_id', '=', account_move_acc_id[inr - 1].line_ids[-1].account_id.id)])
        #     values.append({
        #         'type': 'value',
        #         'account_code': account_move_acc_id[inr - 1].line_ids[-1].account_id.code,
        #         'account_name': account_move_acc_id[inr - 1].line_ids[-1].account_id.name,
        #         'debit': debit,
        #         'credit': credit,
        #     })

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
