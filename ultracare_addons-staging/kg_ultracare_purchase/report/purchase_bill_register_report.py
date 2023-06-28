import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import image_data_uri


class PurchaseBillRegisterReport(models.AbstractModel):
    _name = 'report.kg_ultracare_purchase.purchase_bill_register_wizard'
    _description = 'Purchase Details Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        company_id = data['form'].get('company_id')
        report_type = data['form'].get('report_type')
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
        date_end = data['form'].get('date_to', time.strftime('%Y-%m-%d'))
        browsed_currency_id = data['form'].get('currency_id')
        currency_id = self.env['res.currency'].browse(browsed_currency_id[0])
        browsed_company = self.env['res.company'].browse(company_id[0])
        move_lines = self.env['account.move.line'].search(
            [('move_id.invoice_date', '>=', date_from), ('move_id.invoice_date', '<=', date_end),
             ('move_id.state', '=', 'posted'), ('move_id.move_type', '=', 'in_invoice')])
        if not move_lines:
            raise ValidationError(_('No data in this date range'))
        grand_amount = sum(move_lines.mapped('move_id.amount_total'))
        grand_qty = sum(move_lines.mapped('quantity'))
        data = []
        for rec in move_lines:
            order_no = rec.id
            doc_no = rec.move_id.name

            order_date = rec.move_id.invoice_date

            account_name_tuple = rec.account_id.name
            account_name = ''.join([str(elem) for elem in account_name_tuple])
            account_id_tuple = rec.account_id.code,
            account_id = ','.join([str(element) for element in account_id_tuple])

            debit = rec.debit
            credit = rec.credit
            product = rec.product_id
            customer_name = rec.move_id.partner_id.name
            customer_code = rec.move_id.partner_id.customer_code
            product_item_code = rec.product_id.default_code
            product_description = rec.product_id.name
            unit = rec.product_uom_id.name
            quantity = rec.quantity
            rate = rec.price_unit
            amount = rec.price_subtotal
            amount_bc = rec.currency_id.compute(amount, currency_id)
            purchase_details = {
                'order_no': order_no,
                'doc_no': doc_no,
                'order_date': order_date,
                'ref': order_no,
                'customer_name': customer_name,
                'customer_code': customer_code,
                'account_id': account_id,
                'account_name': account_name,
                'product_item_code': product_item_code,
                'product_description': product_description,
                'product_name': product.name,
                'uom': unit,
                'quantity': quantity,
                'debit': debit,
                'credit': credit,
                'rate': rate,
                'amount': amount,
                'brand': rec.product_id.product_tmpl_id.brand_make,
                'cc': rec.product_id.spare_cc,
                'job_no': '',
                'currency_id': rec.currency_id.name,
                'amount_bc' : amount_bc
            }

            data.append(purchase_details)
        if not data:
            raise ValidationError(_('No data in this date range'))

        return {
            'doc_ids': self.ids,
            'data': data,
            'doc_model': model,
            'currency_id': currency_id.name,
            'company_id': browsed_company.name,
            'logo': browsed_company.logo and image_data_uri(browsed_company.logo),
            'company_details': browsed_company.company_details,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
            'from_date': date_from,
            'to_date': date_end,
            'grand_qty': grand_qty,
            'grand_amount': grand_amount,
        }
