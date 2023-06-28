import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError


class UnpaidInvoiceReport(models.AbstractModel):
    _name = 'report.kg_ultracare_accounting.unpaid_invoice_report_template'
    _description = 'Unpaid Invoice Report'

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
        total_invoice_amount = 0
        partner_id = self.env['res.partner'].search([])
        for customer in partner_id:
            unpaid_account_move_id = self.env['account.move'].search(
                [('date', '>=', date_from), ('payment_state', '!=', 'in_payment'),
                 ('partner_id', '=', customer.id)])
            print(unpaid_account_move_id)
            customer_name = str(customer.name).upper()
            customer_code = str(customer.customer_code).upper()
            unpaid_account_move = {
                'type': 'customer',
                'customer_name': customer_name,
                'customer_code': customer_code,
            }
            if len(unpaid_account_move_id) > 0:
                data.append(unpaid_account_move)
            for vals in unpaid_account_move_id:
                account_type = vals.journal_id.type
                doc_no = vals.name
                date = vals.date
                invoice_amount = vals.amount_total_signed
                due_date = vals.invoice_date_due
                unpaid_account_move = {
                    'type': 'data',
                    'account_type': account_type,
                    'doc_no': doc_no,
                    'date': date,
                    'invoice_amount': invoice_amount,
                    'due_date': due_date,
                }
                data.append(unpaid_account_move)

                total_invoice_amount += invoice_amount
            unpaid_account_move = {
                'type': 'amount',
                'total_invoice_amount': total_invoice_amount
            }
            if total_invoice_amount != 0:
                data.append(unpaid_account_move)
            total_invoice_amount = 0


        return {
            'doc_ids': self.ids,
            'datas': data,
            'doc_model': model,
            'currency_id': currency_id,
            'company_id': browsed_company.name,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
            'to_date': date_from
        }
