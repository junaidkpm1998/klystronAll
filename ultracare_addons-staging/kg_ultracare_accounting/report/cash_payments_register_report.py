import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError


class CashPaymentsRegisterReport(models.AbstractModel):
    _name = 'report.kg_ultracare_accounting.cash_payments_reg_template'
    _description = 'Cash Payments Register Report'

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
        total_credit = 0
        account_payment_id = self.env['account.payment'].search(
            [('date', '>=', date_from), ('date', '<=', date_end), ('state', '!=', ['draft', 'cancel']),
             ('journal_id.type', '=', 'cash')])
        for vals in account_payment_id:
            date = vals.date
            doc_no = vals.name
            reference = vals.ref
            account_code = ''
            account_name = ''
            description = ''
            credit = 0
            debit = 0
            if vals.payment_type == 'outbound':
                account_code = vals.move_id.line_ids[0].account_id.code
                account_name = vals.move_id.line_ids[0].account_id.name
                description = vals.move_id.line_ids[0].name
                credit = vals.move_id.line_ids[0].credit
                debit = vals.move_id.line_ids[0].debit
            if vals.payment_type == 'inbound':
                account_code = vals.move_id.line_ids[0].account_id.code
                account_name = vals.move_id.line_ids[0].account_id.name
                description = vals.move_id.line_ids[0].name
                credit = vals.move_id.line_ids[0].credit
                debit = vals.move_id.line_ids[0].debit

            if credit or debit:
                payment_lines = {
                    'type': 'data',
                    'date': date,
                    'doc_no': doc_no,
                    'reference': reference,
                    'account_code': account_code,
                    'account_name': account_name,
                    'description': description,
                    'credit': credit,
                    'debit': debit,
                }
                data.append(payment_lines)

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
