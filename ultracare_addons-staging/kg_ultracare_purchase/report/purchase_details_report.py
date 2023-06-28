import time
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import image_data_uri


class PurchaseDetailsReport(models.AbstractModel):
    _name = 'report.kg_ultracare_purchase.purchase_register_report_wizard'
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
        purchase_order = self.env['purchase.order.line'].search(
            [('order_id.date_approve', '>=', date_from), ('order_id.date_approve', '<=', date_end),
             ('order_id.state', '=', 'purchase')])
        grand_amount = sum(purchase_order.mapped('order_id.amount_total'))
        grand_qty = sum(purchase_order.mapped('product_uom_qty'))
        data = []
        for rec in purchase_order:
            order_no = rec.id
            order_date = rec.order_id.date_approve
            # ref = rec
            product = rec.product_id
            customer_name = rec.order_id.partner_id.name
            customer_code = rec.order_id.partner_id.customer_code
            product_item_code = rec.product_id.default_code
            product_description = rec.product_id.name
            unit = rec.product_uom.name
            quantity = rec.product_qty
            rate = rec.price_unit
            amount = rec.price_subtotal
            purchase_details = {
                'order_no': order_no,
                'order_date': order_date,
                'ref': order_no,
                'customer_name': customer_name,
                'customer_code': customer_code,
                'product_item_code': product_item_code,
                'product_description': product_description,
                'uom': unit,
                'quantity': quantity,
                'rate': rate,
                'amount': amount,
                'brand': rec.product_id.product_tmpl_id.brand_make,
                'cc': rec.product_id.spare_cc
            }
            data.append(purchase_details)

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
