import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError


class PDCReceiptsRegisterReport(models.AbstractModel):
    _name = 'report.kg_ultracare_accounting.pdc_rec_reg_template'
    _description = 'PDC Receipts Register Report'

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
        sum_debit = 0
        sum_credit = 0
        pdc_id = self.env['pdc.wizard'].search(
            [('payment_date', '>=', date_from), ('payment_date', '<=', date_end),
             ('state', '=', 'done')])
        for vals in pdc_id:
            date = vals.payment_date
            doc_no = vals.name
            ref = vals.reference
            acc_date = vals.invoice_id.date
            account_code = ''
            account_name = ''
            credit = 0
            debit = 0
            if vals.payment_type == 'send_money':
                account_code = vals[0].deposited_debit.account_id.code
                account_name = vals[0].deposited_debit.account_id.name
                credit = vals[0].deposited_debit.credit
                debit = vals[0].deposited_debit.debit
            if vals.payment_type == 'receive_money':
                account_code = vals[0].deposited_debit.account_id.code
                account_name = vals[0].deposited_debit.account_id.name
                credit = vals[0].deposited_debit.credit
                debit = vals[0].deposited_debit.debit

            pdc_vals = {
                'type': 'data',
                'date': date,
                'doc_no': doc_no,
                'acc_date': acc_date,
                'ref': ref,
                'account_code': account_code,
                'account_name': account_name,
                'credit': credit,
                'debit': debit
            }
            data.append(pdc_vals)

            sum_credit += credit
            sum_debit += debit

        pdc_vals = {
            'type': 'amount',
            'sum_debit': sum_debit,
            'sum_credit': sum_credit,
        }
        if sum_credit or sum_debit != 0:
            data.append(pdc_vals)

        sum_debit = 0
        sum_credit = 0

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
