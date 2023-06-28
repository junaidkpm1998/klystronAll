import time
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import image_data_uri


class PurchaseDetailsReport(models.AbstractModel):
    _name = 'report.kg_ultracare_purchase.pending_purchase_report_pdf'
    _description = 'Pending Purchase Report'

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
        data = []
        partner_id = self.env['res.partner'].search([])
        purchase_order = self.env['purchase.order'].search(
            [('date_order', '>=', date_from), ('date_order', '<=', date_end),
             ('state', '!=', 'purchase')])
        customers = purchase_order.mapped('partner_id')
        partners = list(set(customers))
        values = []
        for p in partners:
            p_vals = {
                'level': 1,
                'partner_code': p.ref,
                'partner': p.name,
            }
            values.append(p_vals)
            p_po = purchase_order.filtered(lambda x: x.partner_id.id == p.id)
            products = p_po.mapped('order_line').mapped('product_id')
            for prod in list(set(products)):
                prod_vals = {
                    'level': 2,
                    'product_code': prod.default_code,
                    'product_name': prod.name,
                }
                values.append(prod_vals)

                prod_lines = p_po.mapped('order_line').filtered(lambda x: x.product_id.id == prod.id)
                amount_sum = 0
                qty_sum = 0
                discount = 0
                received = 0
                pending = 0
                for line in prod_lines:
                    line_vals = {
                        'level': 3,
                        'date': line.order_id.date_order,
                        'doc_no': line.order_id.name,
                        'supplier_name': line.order_id.partner_id.name,
                        'item_code': line.product_id.default_code,
                        'description': line.product_id.description,
                        'unit': line.product_uom.name,
                        'rate': line.price_unit,
                        'qty': line.product_qty,
                        # 'discount': line.discount,
                        'amount': line.price_subtotal,
                        'received': line.qty_received,
                    }
                    values.append(line_vals)
                    amount_sum += line.price_subtotal
                    qty_sum += line.product_qty
                    received += line.qty_received
                    pending += line.price_subtotal - line.qty_received
                sum_vals = {
                    'level': 4,
                    'amount_sum': amount_sum,
                    'qty_sum': qty_sum,
                    'received_sum': received,
                    'pending_sum': pending
                }
                values.append(sum_vals)
        return {
            'values': values,
            'from_date': date_from,
            'to_date': date_end,
            'doc_model': model,
            'currency_id': currency_id.name,
            'company_id': browsed_company.name,
            'logo': browsed_company.logo and image_data_uri(browsed_company.logo),
            'company_details': browsed_company.company_details,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name
        }