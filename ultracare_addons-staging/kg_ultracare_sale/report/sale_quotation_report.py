import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_repr, image_data_uri
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class ReportSales(models.AbstractModel):
    _name = 'report.kg_ultracare_sale.sales_statement_documents'
    _description = 'Sales statement Report'

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

        sale_order_search = self.env['sale.order.line'].search(
            [('order_id.date_order', '>=', date_from), ('order_id.date_order', '<=', date_end), ('order_id.state', '=', 'sale')])
        grand_amount = sum(sale_order_search.mapped('order_id.amount_total'))
        grand_qty = sum(sale_order_search.mapped('product_uom_qty'))

        data = []
        for rec in sale_order_search:
            order_no = rec.order_id.name
            order_date = rec.order_id.date_order
            ref = rec.order_id.client_order_ref
            customer_name = rec.order_id.partner_id.name
            customer_code = rec.order_id.partner_id.customer_code
            product_item_code = rec.product_id.default_code
            product_description = rec.name
            unit = rec.product_uom.name
            quantity = rec.product_uom_qty
            rate = rec.price_unit
            amount = rec.price_subtotal
            sale_details = {
                'order_no': order_no,
                'order_date': order_date,
                'ref': ref,
                'customer_name': customer_name,
                'customer_code': customer_code,
                'product_item_code': product_item_code,
                'product_description': product_description,
                'unit': unit,
                'quantity': quantity,
                'rate': rate,
                'amount': amount,
            }
            data.append(sale_details)
        # if not data:
        #     raise ValidationError(_('No data in this date range'))

        return {
            'doc_ids': self.ids,
            'data': data,
            'doc_model': model,
            'currency_id': currency_id,
            'company_id': browsed_company.name,
            'company_details': browsed_company.company_details,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
            'from_date': date_from,
            'to_date': date_end,
            'grand_qty': "{0:.2f}".format(grand_qty),
            'grand_amount': "{0:.2f}".format(grand_amount),
        }

