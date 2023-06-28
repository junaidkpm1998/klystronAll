import time
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import image_data_uri


class PurchaseAnalysisDetailedReport(models.AbstractModel):
    _name = 'report.kg_ultracare_purchase.purchase_analysis_detailed'
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
        date_start = datetime.strptime(date_from, '%Y-%m-%d')
        end_date = datetime.strptime(date_end, '%Y-%m-%d')
        previous_yr_start = date_start - relativedelta(years=1)
        previous_yr_end = end_date - relativedelta(years=1)
        last_yr_start = date_start - relativedelta(years=2)
        last_yr_end = end_date - relativedelta(years=2)
        # print(previous_yr, "PREVVV")
        purchase_order = self.env['purchase.order'].search(
            [('date_order', '>=', last_yr_start), ('date_order', '<=', end_date),
             ('state', '=', 'purchase')])
        customers = purchase_order.mapped('partner_id')
        partners = list(set(customers))
        values = []
        for p in partners:
            # if line.order_id.date_order >= date_start and line.order_id.date_order <= end_date:
            p_vals = {
                'level': 1,
                'partner_code': p.ref,
                'partner': p.name,
            }
            values.append(p_vals)
            p_po = purchase_order.filtered(lambda x: x.partner_id.id == p.id)
            products = p_po.mapped('order_line').mapped('product_id')
            for prod in list(set(products)):
                categ_vals = {
                    'level': 2,
                    'category_code': prod.categ_id.name,
                    'category_name': prod.categ_id.name,
                    'type': dict(prod.product_tmpl_id._fields['kg_internal_type']._description_selection(self.env))[
                            prod.product_tmpl_id.kg_internal_type],
                    # 'type_code' : prod.product_tmpl_id.kg_internal_type_code,
                }
                values.append(categ_vals)
                prod_lines = p_po.mapped('order_line').filtered(lambda x: x.product_id.id == prod.id)
                amount_sum = 0
                qty_sum = 0
                discount = 0
                received = 0
                pending = 0
                for line in prod_lines:
                    lines = {}
                    if line.order_id.date_order >= date_start and line.order_id.date_order <= end_date:
                        lines.update({
                            'level': 3,
                            'item_code': line.product_id.default_code if line.product_id.default_code else '',
                            'description': line.product_id.description if line.product_id.description else line.product_id.name,
                            'unit': line.product_uom.name,
                            'rate': line.price_unit,
                            'qty': line.product_qty,
                            'amount': line.price_subtotal,
                        })
                    else:
                        lines.update({
                            'level': 3,
                            'item_code': '',
                            'description': '',
                            'unit': 0,
                            'rate': 0,
                            'qty': 0,
                            'amount': 0,
                        })
                    if line.order_id.date_order >= previous_yr_start and line.order_id.date_order <= previous_yr_end:
                        lines.update({
                            'level': 3,
                            'unit': line.product_uom.name,
                            'rate': line.price_unit,
                            'prev_qty': line.product_qty,
                            'prev_amount': line.price_subtotal,
                        })
                    else:
                        lines.update({
                            'level': 3,
                            'unit': line.product_uom.name,
                            'rate': line.price_unit,
                            'prev_qty': 0,
                            'prev_amount': 0,
                        })
                    if line.order_id.date_order >= last_yr_start and line.order_id.date_order <= last_yr_end:
                        lines.update({
                            'level': 3,
                            'unit': line.product_uom.name,
                            'rate': line.price_unit,
                            'last_qty': line.product_qty,
                            'last_amount': line.price_subtotal,
                        })
                    else:
                        lines.update({
                            'level': 3,
                            'unit': line.product_uom.name,
                            'rate': line.price_unit,
                            'last_qty': 0,
                            'last_amount': 0,
                        })
                    values.append(lines)
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
        # print(values,"Valuessss")
        # print(type(date_from))
        # date_start = datetime.strptime(date_from, '%Y-%m-%d')
        # date_end = datetime.strptime(date_end, '%Y-%m-%d')
        # from_date = date_start.date()
        # end_date = date_end.date()
        # previous_yr = from_date - relativedelta(years=1)
        # previous_yr_end = end_date - relativedelta(years=1)
        # print(previous_yr, "PPPP")
        # purchase_order_previous = self.env['purchase.order'].search(
        #     [('date_order', '>=', previous_yr), ('date_order', '<=', previous_yr_end),
        #      ('state', '!=', 'purchase')])
        # customers_previous = purchase_order_previous.mapped('partner_id')
        # partners_previous = list(set(customers))
        # for prev in partners_previous:
        #     prev_po = purchase_order.filtered(lambda x: x.partner_id.id == prev.id)
        #     products = prev_po.mapped('order_line').mapped('product_id')
        #     for prod in list(set(products)):
        #         prev_prod_lines = prev_po.mapped('order_line').filtered(lambda x: x.product_id.id == prod.id)
        #         amount_sum = 0
        #         qty_sum = 0
        #         discount = 0
        #         received = 0
        #         pending = 0
        #         for line in prev_prod_lines:
        #             line_val_prev = {
        #                 'level': 3,
        #                 'item_code_prev': line.product_id.default_code,
        #                 'description_prev': line.product_id.description,
        #                 'unit_prev': line.product_uom.name,
        #                 'rate_prev': line.price_unit,
        #                 'qty_prev': line.product_qty,
        #                 'amount_prev': line.price_subtotal,
        #             }
        #             values.append(line_val_prev)
        # for k in values:
        #     print(k,"kkkkk")
        #     a = k.get('level')
        #     print(a)
        # print(values,"VALLLLSSSS")

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
            'company_country': browsed_company.country_id.name,
            'previous_yr_start': previous_yr_start,
            'previous_yr_end': previous_yr_end,
            'last_yr_start': last_yr_start,
            'last_yr_end': last_yr_end
        }
