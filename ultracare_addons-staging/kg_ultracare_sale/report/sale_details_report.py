import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError


class CustomerAnalysisReport(models.AbstractModel):
    _name = 'report.kg_ultracare_sale.sale_details_report_template'
    _description = 'Sales Details Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        company_id = data['form'].get('company_id')

        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
        date_end = data['form'].get('date_to', time.strftime('%Y-%m-%d'))

        date_start = datetime.strptime(date_from, '%Y-%m-%d')
        end_date = datetime.strptime(date_end, '%Y-%m-%d')
        previous_yr_start = date_start - relativedelta(years=1)
        previous_yr_end = end_date - relativedelta(years=1)
        last_yr_start = date_start - relativedelta(years=2)
        last_yr_end = end_date - relativedelta(years=2)

        browsed_currency_id = data['form'].get('currency_id')
        currency_id = self.env['res.currency'].browse(browsed_currency_id[0])
        browsed_company = self.env['res.company'].browse(company_id[0])

        sale_order = self.env['sale.order'].search(
            [('date_order', '>=', last_yr_start), ('date_order', '<=', end_date),
             ('state', '=', 'sale')])
        customers = sale_order.mapped('partner_id')
        partners = list(set(customers))
        values = []
        for p in partners:
            p_vals = {
                'level': 1,
                'customer_code': p.customer_code,
                'customer_name': p.name,
            }
            values.append(p_vals)
            p_po = sale_order.filtered(lambda x: x.partner_id.id == p.id)
            products = p_po.mapped('order_line').mapped('product_id')
            for prod in list(set(products)):
                if prod:
                    categ_vals = {
                        'level': 2,
                        'product_category_code': prod.categ_id.name,
                        'product_category': prod.categ_id.name,
                        'product_group': prod.product_group.name,
                        'product_group_code': prod.product_group.code,
                    }
                    values.append(categ_vals)
                prod_lines = p_po.mapped('order_line').filtered(lambda x: x.product_id.id == prod.id)
                if prod_lines:
                    for line in prod_lines:
                        lines = {}
                        if line.order_id.date_order >= date_start and line.order_id.date_order <= end_date:
                                lines.update({
                                    'level': 3,
                                    'item_code': line.product_id.default_code if line.product_id.default_code else '',
                                    'description': line.name,
                                    'qty': line.product_uom_qty,
                                    'amount': line.price_subtotal,
                                    'profit': line.price_subtotal - (line.purchase_price * line.product_uom_qty),
                                    'profit_percent': line.price_subtotal and (line.price_subtotal - (
                                            line.purchase_price * line.product_uom_qty)) / line.price_subtotal,
                                })
                        else:
                            lines.update({
                                'level': 3,
                                'item_code': '',
                                'description': '',
                                'qty': 0,
                                'amount': 0,
                                'profit': 0,
                                'profit_percent': 0
                            })
                        if line.order_id.date_order >= previous_yr_start and line.order_id.date_order <= previous_yr_end:
                            if line.product_id:
                                lines.update({
                                    'level': 3,
                                    'prev_qty': line.product_uom_qty,
                                    'prev_amount': line.price_subtotal,
                                    'prev_profit': line.price_subtotal - (line.purchase_price * line.product_uom_qty),
                                    'prev_profit_percent': line.price_subtotal and (line.price_subtotal - (
                                            line.purchase_price * line.product_uom_qty)) / line.price_subtotal,
                                })
                        else:
                            lines.update({
                                'level': 3,
                                'prev_qty': 0,
                                'prev_amount': 0,
                                'prev_profit': 0,
                                'prev_profit_percent': 0
                            })
                        if line.order_id.date_order >= last_yr_start and line.order_id.date_order <= last_yr_end:
                            if line.product_id:
                                lines.update({
                                    'level': 3,
                                    'last_qty': line.product_uom_qty,
                                    'last_amount': line.price_subtotal,
                                    'last_profit': line.price_subtotal - (line.purchase_price * line.product_uom_qty),
                                    'last_profit_percent': line.price_subtotal and (line.price_subtotal - (
                                            line.purchase_price * line.product_uom_qty)) / line.price_subtotal,
                                })
                        else:
                            lines.update({
                                'level': 3,
                                'last_qty': 0,
                                'last_amount': 0,
                                'last_profit': 0,
                                'last_profit_percent': 0
                            })
                        values.append(lines)

        # if not data:
        #     raise ValidationError(_('No data in this date range'))

        return {
            'doc_ids': self.ids,
            'datas': values,
            'doc_model': model,
            'currency_id': currency_id,
            'company_id': browsed_company.name,
            'company_details': browsed_company.company_details,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
            'from_date': date_from,
            'to_date': date_end,
            'last_first_year_start': previous_yr_start,
            'last_first_year_end': previous_yr_end,
            'last_second_year_start': last_yr_start,
            'last_second_year_end': last_yr_end,
        }

# import time
# from datetime import datetime
# from dateutil.relativedelta import relativedelta
# from odoo import api, models, _
# from odoo.exceptions import UserError, ValidationError
#
#
# class SalesDetailsReport(models.AbstractModel):
#     _name = 'report.kg_ultracare_sale.sale_details_report_template'
#     _description = 'Sales Details Report'
#
#     # @api.model
#     # def _get_report_values(self, docids, data=None):
#     #     if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
#     #         raise UserError(_("Form content is missing, this report cannot be printed."))
#     #     model = self.env.context.get('active_model')
#     #     company_id = data['form'].get('company_id')
#     #
#     #     date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
#     #     date_end = data['form'].get('date_to', time.strftime('%Y-%m-%d'))
#     #
#     #     date_start = datetime.strptime(date_from, '%Y-%m-%d')
#     #     end_date = datetime.strptime(date_end, '%Y-%m-%d')
#     #     previous_yr_start = date_start - relativedelta(years=1)
#     #     previous_yr_end = end_date - relativedelta(years=1)
#     #     last_yr_start = date_start - relativedelta(years=2)
#     #     last_yr_end = end_date - relativedelta(years=2)
#     #
#     #     browsed_currency_id = data['form'].get('currency_id')
#     #     currency_id = self.env['res.currency'].browse(browsed_currency_id[0])
#     #     browsed_company = self.env['res.company'].browse(company_id[0])
#
#     #     sale_order = self.env['sale.order'].search(
#     #         [('date_order', '>=', last_yr_start), ('date_order', '<=', end_date),
#     #          ('state', '=', 'sale')])
#     #     customers = sale_order.mapped('partner_id')
#     #     partners = list(set(customers))
#     #     values = []
#     #     for p in partners:
#     #         p_vals = {
#     #             'level': 1,
#     #             'customer_code': str(p.customer_code).upper(),
#     #             'customer_name': str(p.name).upper(),
#     #         }
#     #         values.append(p_vals)
#     #         p_po = sale_order.filtered(lambda x: x.partner_id.id == p.id)
#     #         products = p_po.mapped('order_line').mapped('product_id')
#     #         for prod in list(set(products)):
#     #             categ_vals = {
#     #                 'level': 2,
#     #                 'product_category_code': prod.categ_id.name,
#     #                 'product_category': prod.categ_id.name,
#     #                 'product_group': prod.product_group.name,
#     #                 'product_group_code': prod.product_group.code,
#     #             }
#     #             values.append(categ_vals)
#     #             prod_lines = p_po.mapped('order_line').filtered(lambda x: x.product_id.id == prod.id)
#     #             for line in prod_lines:
#     #                 lines = {}
#     #                 if line.order_id.date_order >= date_start and line.order_id.date_order <= end_date:
#     #                     lines.update({
#     #                         'level': 3,
#     #                         'item_code': line.product_id.default_code if line.product_id.default_code else '',
#     #                         'description': line.name,
#     #                         'qty': line.product_uom_qty,
#     #                         'amount': line.price_subtotal,
#     #                         'profit': line.price_subtotal - (line.purchase_price * line.product_uom_qty),
#     #                         'profit_percent': line.price_subtotal and (line.price_subtotal - (
#     #                                     line.purchase_price * line.product_uom_qty)) / line.price_subtotal,
#     #                     })
#     #                 else:
#     #                     lines.update({
#     #                         'level': 3,
#     #                         'item_code': '',
#     #                         'description': '',
#     #                         'qty': 0,
#     #                         'amount': 0,
#     #                         'profit': 0,
#     #                         'profit_percent': 0
#     #                     })
#     #                 if line.order_id.date_order >= previous_yr_start and line.order_id.date_order <= previous_yr_end:
#     #                     lines.update({
#     #                         'level': 3,
#     #                         'prev_qty': line.product_uom_qty,
#     #                         'prev_amount': line.price_subtotal,
#     #                         'prev_profit': line.price_subtotal - (line.purchase_price * line.product_uom_qty),
#     #                         'prev_profit_percent': line.price_subtotal and (line.price_subtotal - (
#     #                                     line.purchase_price * line.product_uom_qty)) / line.price_subtotal,
#     #                     })
#     #                 else:
#     #                     lines.update({
#     #                         'level': 3,
#     #                         'prev_qty': 0,
#     #                         'prev_amount': 0,
#     #                         'prev_profit': 0,
#     #                         'prev_profit_percent': 0
#     #                     })
#     #                 if line.order_id.date_order >= last_yr_start and line.order_id.date_order <= last_yr_end:
#     #                     lines.update({
#     #                         'level': 3,
#     #                         'last_qty': line.product_uom_qty,
#     #                         'last_amount': line.price_subtotal,
#     #                         'last_profit': line.price_subtotal - (line.purchase_price * line.product_uom_qty),
#     #                         'last_profit_percent': line.price_subtotal and (line.price_subtotal - (
#     #                                     line.purchase_price * line.product_uom_qty)) / line.price_subtotal,
#     #                     })
#     #                 else:
#     #                     lines.update({
#     #                         'level': 3,
#     #                         'last_qty': 0,
#     #                         'last_amount': 0,
#     #                         'last_profit': 0,
#     #                         'last_profit_percent': 0
#     #                     })
#     #                 values.append(lines)
#     #
#     #     if not data:
#     #         raise ValidationError(_('No data in this date range'))
#
#     # @api.model
#     # def _get_report_values(self, docids, data=None):
#     #     if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
#     #         raise UserError(_("Form content is missing, this report cannot be printed."))
#     #     model = self.env.context.get('active_model')
#     #     company_id = data['form'].get('company_id')
#     #
#     #     date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
#     #     date_end = data['form'].get('date_to', time.strftime('%Y-%m-%d'))
#     #
#     #     date_start = datetime.strptime(date_from, '%Y-%m-%d')
#     #     end_date = datetime.strptime(date_end, '%Y-%m-%d')
#     #
#     #     previous_yr_start = date_start - relativedelta(years=1)
#     #     previous_yr_end = end_date - relativedelta(years=1)
#     #     last_yr_start = date_start - relativedelta(years=2)
#     #     last_yr_end = end_date - relativedelta(years=2)
#     #
#     #     browsed_currency_id = data['form'].get('currency_id')
#     #     currency_id = self.env['res.currency'].browse(browsed_currency_id[0])
#     #     browsed_company = self.env['res.company'].browse(company_id[0])
#     #
#     #     partner_id = self.env['res.partner'].search([])
#     #     data_list = []
#     #     sum_sales_amount = 0
#     #     sum_quantity = 0
#     #     for customer in partner_id:
#     #         account_line = self.env['account.move.line'].search(
#     #             [('move_id.invoice_date', '>=', date_from), ('move_id.invoice_date', '<=', date_end),
#     #              ('move_id.state', '=', 'posted'), ('move_id.partner_id', '=', customer.id),
#     #             ], order='product_id asc')
#     #
#     #         customer_name = str(customer.name).upper()
#     #         customer_code = str(customer.customer_code).upper()
#     #         account_move_line = {'type': 'customer',
#     #                              'customer_name': customer_name,
#     #                              'customer_code': customer_code,
#     #                              }
#     #         if len(account_line) > 0:
#     #             data_list.append(account_move_line)
#     #
#     #         if len(account_line) > 0:
#     #             product = account_line[0].product_id.id
#     #             inr = 0
#     #             qty = 0
#     #             amount = 0
#     #             profit = 0
#     #             profit_percent = 0
#     #             prev_qty = 0
#     #             prev_amount = 0
#     #             prev_profit = 0
#     #             prev_profit_percent = 0
#     #             last_qty = 0
#     #             last_amount = 0
#     #             last_profit = 0
#     #             last_profit_percent = 0
#     #
#     #             while (inr < len(account_line)):
#     #                 if account_line[inr].product_id.id == product:
#     #                     qty += account_line[inr].quantity
#     #                     amount += account_line[inr].price_subtotal
#     #                     profit += account_line[inr].price_subtotal - (
#     #                             account_line[inr].sale_line_ids.purchase_price * account_line[inr].quantity)
#     #                     profit_percent += account_line[inr].price_subtotal and (account_line[inr].price_subtotal - (
#     #                             account_line[inr].sale_line_ids.purchase_price * account_line[inr].quantity)) / \
#     #                                       account_line[inr].price_subtotal
#     #
#     #                     prev_qty += account_line[inr].quantity
#     #                     prev_amount += account_line[inr].price_subtotal
#     #                     prev_profit += account_line[inr].price_subtotal - (
#     #                             account_line[inr].sale_line_ids.purchase_price * account_line[inr].quantity)
#     #                     prev_profit_percent += account_line[inr].price_subtotal and (
#     #                             account_line[inr].price_subtotal - (
#     #                             account_line[inr].sale_line_ids.purchase_price * account_line[inr].quantity)) / \
#     #                                            account_line[
#     #                                                inr].price_subtotal
#     #
#     #                     last_qty += account_line[inr].quantity
#     #                     last_amount += account_line[inr].price_subtotal
#     #                     last_profit += account_line[inr].price_subtotal - (
#     #                             account_line[inr].sale_line_ids.purchase_price * account_line[inr].quantity)
#     #                     last_profit_percent += account_line[inr].price_subtotal and (
#     #                             account_line[inr].price_subtotal - (
#     #                             account_line[inr].sale_line_ids.purchase_price * account_line[inr].quantity)) / \
#     #                                            account_line[
#     #                                                inr].price_subtotal
#     #
#     #                 else:
#     #                     rtn_line = self.env['account.move.line'].search(
#     #                         [('move_id.invoice_date', '<=', date_end), ('move_id.invoice_date', '>=', date_from),
#     #                          ('move_id.state', '=', 'posted'),
#     #                          ('product_id', '=', product)])
#     #                     description = rtn_line[0].name
#     #                     #             vart = []
#     #                     #             if rtn_line.product_id.product_template_variant_value_ids:
#     #                     #                 for var in rtn_line.product_id.product_template_variant_value_ids:
#     #                     #                     vart.append(var.name)
#     #                     #             variance = ','.join([str(elem) for elem in vart])
#     #                     #             sale_date = rtn_line[0].sale_line_ids.order_id.date_order
#     #                     #
#     #                     data_list.append(
#     #                         {
#     #                             'type': 'data',
#     #                             'product_category_code': str(
#     #                                 account_line[inr - 1].product_id.categ_id.parent_id.name).upper(),
#     #                             'product_category': str(account_line[inr - 1].product_id.categ_id.name).upper(),
#     #                             'product_group_code': str(account_line[inr - 1].product_id.product_group.code).upper(),
#     #                             'product_group': str(account_line[inr - 1].product_id.product_group.name).upper(),
#     #                             'item_code': str(account_line[inr - 1].product_id.default_code).upper(),
#     #                             'description': description,
#     #                             'amount': amount,
#     #                             'qty': qty,
#     #                             'profit': profit,
#     #                             'profit_percent': profit_percent,
#     #                         })
#     #                     #             sum_sales_amount += sales_amount
#     #                     #             sum_quantity += quantity
#     #                     #
#     #                     product = account_line[inr].product_id.id
#     #                     profit = 0
#     #                     profit_percent = 0
#     #                     prev_qty = 0
#     #                     prev_amount = 0
#     #                     prev_profit = 0
#     #                     prev_profit_percent = 0
#     #                     last_qty = 0
#     #                     last_amount = 0
#     #                     last_profit = 0
#     #                     last_profit_percent = 0
#     #
#     #                     qty += account_line[inr].quantity
#     #                     amount += account_line[inr].price_subtotal
#     #                     profit += account_line[inr].price_subtotal - (
#     #                             account_line[inr].sale_line_ids.purchase_price * account_line[inr].quantity)
#     #                     profit_percent += account_line[inr].price_subtotal and (account_line[inr].price_subtotal - (
#     #                             account_line[inr].sale_line_ids.purchase_price * account_line[inr].quantity)) / \
#     #                                       account_line[inr].price_subtotal
#     #
#     #                     prev_qty += account_line[inr].quantity
#     #                     prev_amount += account_line[inr].price_subtotal
#     #                     prev_profit += account_line[inr].price_subtotal - (
#     #                             account_line[inr].sale_line_ids.purchase_price * account_line[inr].quantity)
#     #                     prev_profit_percent += account_line[inr].price_subtotal and (
#     #                             account_line[inr].price_subtotal - (
#     #                             account_line[inr].sale_line_ids.purchase_price * account_line[inr].quantity)) / \
#     #                                            account_line[
#     #                                                inr].price_subtotal
#     #
#     #                     last_qty += account_line[inr].quantity
#     #                     last_amount += account_line[inr].price_subtotal
#     #                     last_profit += account_line[inr].price_subtotal - (
#     #                             account_line[inr].sale_line_ids.purchase_price * account_line[inr].quantity)
#     #                     last_profit_percent += account_line[inr].price_subtotal and (
#     #                             account_line[inr].price_subtotal - (
#     #                             account_line[inr].sale_line_ids.purchase_price * account_line[inr].quantity)) / \
#     #                                            account_line[
#     #                                                inr].price_subtotal
#     #
#     #                 inr += 1
#     #
#     #             rtn_line = self.env['account.move.line'].search(
#     #                 [('move_id.invoice_date', '<=', date_end), ('move_id.invoice_date', '>=', date_from),
#     #                  ('move_id.state', '=', 'posted'), ('product_id', '=', account_line[inr - 1].product_id.id),
#     #                  ])
#     #             #     vart = []
#     #             #     if rtn_line.product_id.product_template_variant_value_ids:
#     #             #         for var in rtn_line.product_id.product_template_variant_value_ids:
#     #             #             vart.append(var.name)
#     #             #     variance = ','.join([str(elem) for elem in vart])
#     #             description = rtn_line[0].name
#     #             data_list.append(
#     #                 {
#     #                     'type': 'data',
#     #                     'product_category_code': str(
#     #                         account_line[inr - 1].product_id.categ_id.parent_id.name).upper(),
#     #                     'product_category': str(account_line[inr - 1].product_id.categ_id.name).upper(),
#     #                     'product_group_code': str(account_line[inr - 1].product_id.product_group.code).upper(),
#     #                     'product_group': str(account_line[inr - 1].product_id.product_group.name).upper(),
#     #                     'item_code': str(account_line[inr - 1].product_id.default_code).upper(),
#     #                     'description': description,
#     #                     'amount': amount,
#     #                     'qty': qty,
#     #                     'profit': profit,
#     #                     'profit_percent': profit_percent,
#     #                 })
#     #
#     #             # sum_sales_amount += sales_amount
#     #             # sum_quantity += quantity
#     #
#     #         # if sum_sales_amount != 0:
#     #         #     data_list.append({
#     #         #         'type': 'amount',
#     #         #         'total_sale': sum_sales_amount,
#     #         #         'total_qty': sum_quantity
#     #         #     })
#     #         # sum_sales_amount = 0
#     #         # sum_quantity = 0
#     #
#     #     if not data_list:
#     #         raise ValidationError(_('No data in this date range'))
#     #
#     #     return {
#     #         'doc_ids': self.ids,
#     #         'datas': data_list,
#     #         'doc_model': model,
#     #         'currency_id': currency_id,
#     #         'company_id': browsed_company.name,
#     #         'company_details': browsed_company.company_details,
#     #         'company_zip': browsed_company.zip,
#     #         'company_state': browsed_company.state_id.name,
#     #         'company_country': browsed_company.country_id.name,
#     #         'from_date': date_from,
#     #         'to_date': date_end,
#     #         'last_first_year_start': previous_yr_start,
#     #         'last_first_year_end': previous_yr_end,
#     #         'last_second_year_start': last_yr_start,
#     #         'last_second_year_end': last_yr_end,
#     #     }
#
#     # import time
#     # from datetime import datetime
#     # from dateutil.relativedelta import relativedelta
#     # from odoo import api, models, _
#     # from odoo.exceptions import UserError, ValidationError
#     #
#     #
#     # class CustomerAnalysisReport(models.AbstractModel):
#     #     _name = 'report.kg_ultracare_sale.sale_details_report_template'
#     #     _description = 'Sales Details Report'
#     #
#     @api.model
#     def _get_report_values(self, docids, data=None):
#         if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
#             raise UserError(_("Form content is missing, this report cannot be printed."))
#         model = self.env.context.get('active_model')
#         company_id = data['form'].get('company_id')
#
#         date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
#         date_end = data['form'].get('date_to', time.strftime('%Y-%m-%d'))
#
#         # date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
#         # date_end = data['form'].get('date_to', time.strftime('%Y-%m-%d'))
#
#         date_start = datetime.strptime(date_from, '%Y-%m-%d')
#         end_date = datetime.strptime(date_end, '%Y-%m-%d')
#         # previous_yr_start = date_start - relativedelta(years=1)
#         # previous_yr_end = end_date - relativedelta(years=1)
#         # last_yr_start = date_start - relativedelta(years=2)
#         # last_yr_end = end_date - relativedelta(years=2)
#
#         x = data['form'].get('last_first_year_start', time.strftime('%Y-%m-%d'))
#         previous_yr_start = datetime.strptime(x, '%Y-%m-%d')
#         y = data['form'].get('last_first_year_end', time.strftime('%Y-%m-%d'))
#         previous_yr_end = datetime.strptime(y, '%Y-%m-%d')
#         a = data['form'].get('last_second_year_start', time.strftime('%Y-%m-%d'))
#         last_yr_start = datetime.strptime(a, '%Y-%m-%d')
#         b = data['form'].get('last_second_year_end', time.strftime('%Y-%m-%d'))
#         last_yr_end = datetime.strptime(b, '%Y-%m-%d')
#
#         browsed_currency_id = data['form'].get('currency_id')
#         currency_id = self.env['res.currency'].browse(browsed_currency_id[0])
#         browsed_company = self.env['res.company'].browse(company_id[0])
#         #
#         #         sale_order = self.env['sale.order'].search(
#         #             [('date_order', '>=', last_yr_start), ('date_order', '<=', end_date),
#         #              ('state', '=', 'sale')])
#         #         customers = sale_order.mapped('partner_id')
#         #         partners = list(set(customers))
#         #         values = []
#         #         for p in partners:
#         #             p_vals = {
#         #                 'level': 1,
#         #                 'customer_code': str(p.customer_code).upper(),
#         #                 'customer_name': str(p.name).upper(),
#         #             }
#         #             values.append(p_vals)
#         #             p_po = sale_order.filtered(lambda x: x.partner_id.id == p.id)
#         #             products = p_po.mapped('order_line').mapped('product_id')
#         #             for prod in list(set(products)):
#         #                 categ_vals = {
#         #                     'level': 2,
#         #                     'product_category_code': prod.categ_id.name,
#         #                     'product_category': prod.categ_id.name,
#         #                     'product_group': prod.product_group.name,
#         #                     'product_group_code': prod.product_group.code,
#         #                 }
#         #                 values.append(categ_vals)
#         #                 prod_lines = p_po.mapped('order_line').filtered(lambda x: x.product_id.id == prod.id)
#         #                 for line in prod_lines:
#         #                     lines = {}
#         #                     if line.order_id.date_order >= date_start and line.order_id.date_order <= end_date:
#         #                         lines.update({
#         #                             'level': 3,
#         #                             'item_code': line.product_id.default_code if line.product_id.default_code else '',
#         #                             'description': line.name,
#         #                             'qty': line.product_uom_qty,
#         #                             'amount': line.price_subtotal,
#         #                             'profit': line.price_subtotal - (line.purchase_price * line.product_uom_qty),
#         #                             'profit_percent': line.price_subtotal and (line.price_subtotal - (line.purchase_price * line.product_uom_qty))/line.price_subtotal,
#         #                         })
#         #                     else:
#         #                         lines.update({
#         #                             'level': 3,
#         #                             'item_code': '',
#         #                             'description': '',
#         #                             'qty': 0,
#         #                             'amount': 0,
#         #                             'profit': 0,
#         #                             'profit_percent': 0
#         #                         })
#         #                     if line.order_id.date_order >= previous_yr_start and line.order_id.date_order <= previous_yr_end:
#         #                         lines.update({
#         #                             'level': 3,
#         #                             'prev_qty': line.product_uom_qty,
#         #                             'prev_amount': line.price_subtotal,
#         #                             'prev_profit': line.price_subtotal - (line.purchase_price * line.product_uom_qty),
#         #                             'prev_profit_percent': line.price_subtotal and (line.price_subtotal - (line.purchase_price * line.product_uom_qty))/line.price_subtotal,
#         #                         })
#         #                     else:
#         #                         lines.update({
#         #                             'level': 3,
#         #                             'prev_qty': 0,
#         #                             'prev_amount': 0,
#         #                             'prev_profit': 0,
#         #                             'prev_profit_percent': 0
#         #                         })
#         #                     if line.order_id.date_order >= last_yr_start and line.order_id.date_order <= last_yr_end:
#         #                         lines.update({
#         #                             'level': 3,
#         #                             'last_qty': line.product_uom_qty,
#         #                             'last_amount': line.price_subtotal,
#         #                             'last_profit': line.price_subtotal - (line.purchase_price * line.product_uom_qty),
#         #                             'last_profit_percent': line.price_subtotal and (line.price_subtotal - (line.purchase_price * line.product_uom_qty))/line.price_subtotal,
#         #                         })
#         #                     else:
#         #                         lines.update({
#         #                             'level': 3,
#         #                             'last_qty': 0,
#         #                             'last_amount': 0,
#         #                             'last_profit': 0,
#         #                             'last_profit_percent': 0
#         #                         })
#         #                     values.append(lines)
#
#         # partner_id = self.env['res.partner'].search([])
#         # data_list = []
#         # sum_sales_amount = 0
#         # sum_quantity = 0
#         # for customer in partner_id:
#         #     sale_order = self.env['sale.order'].search(
#         #         [('date_order', '>=', last_yr_start), ('date_order', '<=', end_date),
#         #          ('state', '=', 'sale'), ('partner_id', '=', customer.id)], )
#         #
#         #     customer_name = str(customer.name).upper()
#         #     customer_code = str(customer.customer_code).upper()
#         #     account_move_line = {'type': 'customer',
#         #                          'customer_name': customer_name,
#         #                          'customer_code': customer_code,
#         #                          }
#         #     if len(sale_order) > 0:
#         #         data_list.append(account_move_line)
#         #
#         #     if len(sale_order) > 0:
#         #         for sale_order in sale_order:
#         #             product = sale_order[0].order_line.product_id.id
#         #             inr = 0
#         #             qty = 0
#         #             amount = 0
#         #             profit = 0
#         #             profit_percent = 0
#         #             prev_qty = 0
#         #             prev_amount = 0
#         #             prev_profit = 0
#         #             prev_profit_percent = 0
#         #             last_qty = 0
#         #             last_amount = 0
#         #             last_profit = 0
#         #             last_profit_percent = 0
#         #
#         #             while (inr < len(sale_order)):
#         #                 if sale_order[inr].product_id.id == product:
#         #                     qty += sale_order[inr].quantity
#         #                     amount += sale_order[inr].price_subtotal
#         #                     profit += sale_order[inr].price_subtotal - (sale_order[inr].purchase_price * sale_order[inr].quantity)
#         #                     profit_percent += sale_order[inr].price_subtotal and (sale_order[inr].price_subtotal - (
#         #                                         sale_order[inr].purchase_price * sale_order[inr].quantity)) / sale_order[inr].price_subtotal
#         #
#         #                     prev_qty += sale_order[inr].quantity
#         #                     prev_amount += sale_order[inr].price_subtotal
#         #                     prev_profit += sale_order[inr].price_subtotal - (sale_order[inr].purchase_price * sale_order[inr].quantity)
#         #                     prev_profit_percent += sale_order[inr].price_subtotal and (sale_order[inr].price_subtotal - (
#         #                                         sale_order[inr].purchase_price * sale_order[inr].quantity)) / sale_order[inr].price_subtotal
#         #
#         #                     last_qty += sale_order[inr].quantity
#         #                     last_amount += sale_order[inr].price_subtotal
#         #                     last_profit += sale_order[inr].price_subtotal - (sale_order[inr].purchase_price * sale_order[inr].quantity)
#         #                     last_profit_percent += sale_order[inr].price_subtotal and (sale_order[inr].price_subtotal - (
#         #                                         sale_order[inr].purchase_price * sale_order[inr].quantity)) / sale_order[inr].price_subtotal
#         #                 else:
#         #                     rtn_line = self.env['sale.order'].search(
#         #                         [('date_order', '>=', last_yr_start), ('date_order', '<=', end_date),
#         #                          ('state', '=', 'sale'), ('order_line.product_id', '=', product)])
#         #
#         #                     prod_lines = rtn_line.mapped('order_line').filtered(lambda x: x.product_id.id == product.id)
#         #                     for line in prod_lines:
#         #                         lines = {}
#         #                         if line.order_id.date_order >= date_start and line.order_id.date_order <= end_date:
#         #                             lines.update({
#         #                                 'level': 3,
#         #                                 'item_code': line.product_id.default_code if line.product_id.default_code else '',
#         #                                 'description': line.name,
#         #                                 'qty': qty,
#         #                                 'amount': amount,
#         #                                 'profit': profit,
#         #                                 'profit_percent': profit_percent,
#         #                             })
#         #                         else:
#         #                             lines.update({
#         #                                 'level': 3,
#         #                                 'item_code': '',
#         #                                 'description': '',
#         #                                 'qty': 0,
#         #                                 'amount': 0,
#         #                                 'profit': 0,
#         #                                 'profit_percent': 0
#         #                             })
#         #                         if line.order_id.date_order >= previous_yr_start and line.order_id.date_order <= previous_yr_end:
#         #                             lines.update({
#         #                                 'level': 3,
#         #                                 'prev_qty': prev_qty,
#         #                                 'prev_amount': prev_amount,
#         #                                 'prev_profit': prev_profit,
#         #                                 'prev_profit_percent': prev_profit_percent,
#         #                             })
#         #                         else:
#         #                             lines.update({
#         #                                 'level': 3,
#         #                                 'prev_qty': 0,
#         #                                 'prev_amount': 0,
#         #                                 'prev_profit': 0,
#         #                                 'prev_profit_percent': 0
#         #                             })
#         #                         if line.order_id.date_order >= last_yr_start and line.order_id.date_order <= last_yr_end:
#         #                             lines.update({
#         #                                 'level': 3,
#         #                                 'last_qty': last_qty,
#         #                                 'last_amount': last_amount,
#         #                                 'last_profit': last_profit,
#         #                                 'last_profit_percent': last_profit_percent,
#         #                             })
#         #                         else:
#         #                             lines.update({
#         #                                 'level': 3,
#         #                                 'last_qty': 0,
#         #                                 'last_amount': 0,
#         #                                 'last_profit': 0,
#         #                                 'last_profit_percent': 0
#         #                             })
#         #                         data_list.append(lines)
#
#         #                         product = sale_order[inr].product_id.id
#         #                         qty = 0
#         #                         amount = 0
#         #                         profit = 0
#         #                         profit_percent = 0
#         #                         prev_qty = 0
#         #                         prev_amount = 0
#         #                         prev_profit = 0
#         #                         prev_profit_percent = 0
#         #                         last_qty = 0
#         #                         last_amount = 0
#         #                         last_profit = 0
#         #                         last_profit_percent = 0
#         #                         qty += sale_order[inr].quantity
#         #                         amount += sale_order[inr].price_subtotal
#         #                         profit += sale_order[inr].price_subtotal - (
#         #                                     sale_order[inr].purchase_price * sale_order[inr].quantity)
#         #                         profit_percent += sale_order[inr].price_subtotal and (sale_order[inr].price_subtotal - (
#         #                                 sale_order[inr].purchase_price * sale_order[inr].quantity)) / sale_order[
#         #                                               inr].price_subtotal
#         #
#         #                         prev_qty += sale_order[inr].quantity
#         #                         prev_amount += sale_order[inr].price_subtotal
#         #                         prev_profit += sale_order[inr].price_subtotal - (
#         #                                     sale_order[inr].purchase_price * sale_order[inr].quantity)
#         #                         prev_profit_percent += sale_order[inr].price_subtotal and (
#         #                                     sale_order[inr].price_subtotal - (
#         #                                     sale_order[inr].purchase_price * sale_order[inr].quantity)) / sale_order[
#         #                                                    inr].price_subtotal
#         #
#         #                         last_qty += sale_order[inr].quantity
#         #                         last_amount += sale_order[inr].price_subtotal
#         #                         last_profit += sale_order[inr].price_subtotal - (
#         #                                     sale_order[inr].purchase_price * sale_order[inr].quantity)
#         #                         last_profit_percent += sale_order[inr].price_subtotal and (
#         #                                     sale_order[inr].price_subtotal - (
#         #                                     sale_order[inr].purchase_price * sale_order[inr].quantity)) / sale_order[
#         #                                                    inr].price_subtotal
#         #                 inr += 1
#         #             rtn_line = self.env['sale.order'].search(
#         #                 [('date_order', '>=', last_yr_start), ('date_order', '<=', end_date),
#         #                  ('state', '=', 'sale'), ('order_line.product_id', '=', sale_order[inr - 1].product_id.id)])
#         #
#         #             prod_lines = rtn_line.mapped('order_line').filtered(lambda x: x.product_id.id == product.id)
#         #             for line in prod_lines:
#         #                 lines = {}
#         #                 if line.order_id.date_order >= date_start and line.order_id.date_order <= end_date:
#         #                     lines.update({
#         #                         'level': 3,
#         #                         'item_code': line.product_id.default_code if line.product_id.default_code else '',
#         #                         'description': line.name,
#         #                         'qty': qty,
#         #                         'amount': amount,
#         #                         'profit': profit,
#         #                         'profit_percent': profit_percent,
#         #                     })
#         #                 else:
#         #                     lines.update({
#         #                         'level': 3,
#         #                         'item_code': '',
#         #                         'description': '',
#         #                         'qty': 0,
#         #                         'amount': 0,
#         #                         'profit': 0,
#         #                         'profit_percent': 0
#         #                     })
#         #                 if line.order_id.date_order >= previous_yr_start and line.order_id.date_order <= previous_yr_end:
#         #                     lines.update({
#         #                         'level': 3,
#         #                         'prev_qty': prev_qty,
#         #                         'prev_amount': prev_amount,
#         #                         'prev_profit': prev_profit,
#         #                         'prev_profit_percent': prev_profit_percent,
#         #                     })
#         #                 else:
#         #                     lines.update({
#         #                         'level': 3,
#         #                         'prev_qty': 0,
#         #                         'prev_amount': 0,
#         #                         'prev_profit': 0,
#         #                         'prev_profit_percent': 0
#         #                     })
#         #                 if line.order_id.date_order >= last_yr_start and line.order_id.date_order <= last_yr_end:
#         #                     lines.update({
#         #                         'level': 3,
#         #                         'last_qty': last_qty,
#         #                         'last_amount': last_amount,
#         #                         'last_profit': last_profit,
#         #                         'last_profit_percent': last_profit_percent,
#         #                     })
#         #                 else:
#         #                     lines.update({
#         #                         'level': 3,
#         #                         'last_qty': 0,
#         #                         'last_amount': 0,
#         #                         'last_profit': 0,
#         #                         'last_profit_percent': 0
#         #                     })
#         #                 data_list.append(lines)
#
#         #         # if sum_sales_amount != 0:
#         #         #     data_list.append({
#         #         #         'type': 'amount',
#         #         #         'total_sale': sum_sales_amount,
#         #         #         'total_qty': sum_quantity
#         #         #     })
#         #         # sum_sales_amount = 0
#         #         # sum_quantity = 0
#
#         partner_id = self.env['res.partner'].search([])
#         data_list = []
#         for customer in partner_id:
#             account_line = self.env['account.move.line'].search(
#                 [('move_id.invoice_date', '>=', date_from), ('move_id.invoice_date', '<=', date_end),
#                  ('move_id.state', '=', 'posted'), ('move_id.partner_id', '=', customer.id),
#                  ('move_id.move_type', '=', 'out_invoice')], order='product_id asc')
#
#             customer_name = str(customer.name).upper()
#             customer_code = str(customer.customer_code).upper()
#             account_move_line = {'level': 1,
#                                  'customer_name': customer_name,
#                                  'customer_code': customer_code,
#                                  }
#             if len(account_line) > 0:
#                 data_list.append(account_move_line)
#
#             if len(account_line) > 0:
#                 product = account_line[0].product_id.id
#                 inr = 0
#                 qty = 0
#                 amount = 0
#                 profit = 0
#                 profit_percent = 0
#                 prev_qty = 0
#                 prev_amount = 0
#                 prev_profit = 0
#                 prev_profit_percent = 0
#                 last_qty = 0
#                 last_amount = 0
#                 last_profit = 0
#                 last_profit_percent = 0
#                 while (inr < len(account_line)):
#                     if account_line[inr].product_id.id == product:
#                         qty += account_line[inr].quantity
#                         amount += account_line[inr].price_subtotal
#                         profit += account_line[inr].price_subtotal - (
#                                 account_line[inr].sale_line_ids.purchase_price * account_line[inr].quantity)
#                         profit_percent += account_line[inr].price_subtotal and (account_line[inr].price_subtotal - (
#                                 account_line[inr].sale_line_ids.purchase_price * account_line[inr].quantity)) / \
#                                           account_line[
#                                               inr].price_subtotal
#
#                         prev_qty += account_line[inr].quantity
#                         prev_amount += account_line[inr].price_subtotal
#                         prev_profit += account_line[inr].price_subtotal - (
#                                 account_line[inr].sale_line_ids.purchase_price * account_line[inr].quantity)
#                         prev_profit_percent += account_line[inr].price_subtotal and (
#                                 account_line[inr].price_subtotal - (
#                                 account_line[inr].sale_line_ids.purchase_price * account_line[inr].quantity)) / \
#                                                account_line[
#                                                    inr].price_subtotal
#
#                         last_qty += account_line[inr].quantity
#                         last_amount += account_line[inr].price_subtotal
#                         last_profit += account_line[inr].price_subtotal - (
#                                 account_line[inr].sale_line_ids.purchase_price * account_line[inr].quantity)
#                         last_profit_percent += account_line[inr].price_subtotal and (
#                                 account_line[inr].price_subtotal - (
#                                 account_line[inr].sale_line_ids.purchase_price * account_line[inr].quantity)) / \
#                                                account_line[
#                                                    inr].price_subtotal
#                     else:
#                         rtn_line = self.env['account.move.line'].search(
#                             [('move_id.invoice_date', '<=', date_end), ('move_id.invoice_date', '>=', date_from),
#                              ('move_id.state', '=', 'posted'),
#                              ('product_id', '=', product), ('move_id.move_type', '=', 'out_invoice')])
#                         for line in rtn_line:
#                             description = line[0].name
#                             lines = {}
#                             if line.move_id.invoice_date >= date_start.date() and line.move_id.invoice_date <= end_date.date():
#                                 lines.update({
#                                     'level': 3,
#                                     'product_category_code': str(
#                                         account_line[inr - 1].product_id.categ_id.parent_id.name).upper(),
#                                     'product_category': str(account_line[inr - 1].product_id.categ_id.name).upper(),
#                                     'product_group_code': str(
#                                         account_line[inr - 1].product_id.product_group.code).upper(),
#                                     'product_group': str(account_line[inr - 1].product_id.product_group.name).upper(),
#                                     'item_code': str(account_line[inr - 1].product_id.default_code).upper(),
#                                     'description': description,
#                                     'qty': qty,
#                                     'amount': amount,
#                                     'profit': profit,
#                                     'profit_percent': profit_percent,
#                                 })
#                             else:
#                                 lines.update({
#                                     'level': 3,
#                                     'item_code': '',
#                                     'description': '',
#                                     'qty': 0,
#                                     'amount': 0,
#                                     'profit': 0,
#                                     'profit_percent': 0
#                                 })
#                             if line.move_id.invoice_date >= previous_yr_start.date() and line.move_id.invoice_date <= previous_yr_end.date():
#                                 lines.update({
#                                     'level': 3,
#                                     'prev_qty': prev_qty,
#                                     'prev_amount': prev_amount,
#                                     'prev_profit': prev_profit,
#                                     'prev_profit_percent': prev_profit_percent,
#                                 })
#                             else:
#                                 lines.update({
#                                     'level': 3,
#                                     'prev_qty': 0,
#                                     'prev_amount': 0,
#                                     'prev_profit': 0,
#                                     'prev_profit_percent': 0
#                                 })
#                             if line.move_id.invoice_date >= last_yr_start.date() and line.move_id.invoice_date <= last_yr_end.date():
#                                 lines.update({
#                                     'level': 3,
#                                     'last_qty': last_qty,
#                                     'last_amount': last_amount,
#                                     'last_profit': last_profit,
#                                     'last_profit_percent': last_profit_percent,
#                                 })
#                             else:
#                                 lines.update({
#                                     'level': 3,
#                                     'last_qty': 0,
#                                     'last_amount': 0,
#                                     'last_profit': 0,
#                                     'last_profit_percent': 0
#                                 })
#                             data_list.append(lines)
#
#                             product = account_line[inr].product_id.id
#                             qty = 0
#                             amount = 0
#                             profit = 0
#                             profit_percent = 0
#                             prev_qty = 0
#                             prev_amount = 0
#                             prev_profit = 0
#                             prev_profit_percent = 0
#                             last_qty = 0
#                             last_amount = 0
#                             last_profit = 0
#                             last_profit_percent = 0
#
#                     inr += 1
#
#                 rtn_line = self.env['account.move.line'].search(
#                     [('move_id.invoice_date', '<=', date_end), ('move_id.invoice_date', '>=', date_from),
#                      ('move_id.state', '=', 'posted'), ('product_id', '=', account_line[inr - 1].product_id.id),
#                      ('move_id.move_type', '=', 'out_invoice')])
#
#                 # prod_lines = rtn_line.mapped('order_line').filtered(lambda x: x.product_id.id == product.id)
#                 for line in rtn_line:
#                     description = line[0].name
#                     lines = {}
#                     if line.move_id.invoice_date >= date_start.date() and line.move_id.invoice_date <= end_date.date():
#                         lines.update({
#                             'level': 3,
#                             'product_category_code': str(
#                                 account_line[inr - 1].product_id.categ_id.parent_id.name).upper(),
#                             'product_category': str(account_line[inr - 1].product_id.categ_id.name).upper(),
#                             'product_group_code': str(account_line[inr - 1].product_id.product_group.code).upper(),
#                             'product_group': str(account_line[inr - 1].product_id.product_group.name).upper(),
#                             'item_code': str(account_line[inr - 1].product_id.default_code).upper(),
#                             'description': description,
#                             'qty': qty,
#                             'amount': amount,
#                             'profit': profit,
#                             'profit_percent': profit_percent,
#                         })
#                     else:
#                         lines.update({
#                             'level': 3,
#                             'item_code': '',
#                             'description': '',
#                             'qty': 0,
#                             'amount': 0,
#                             'profit': 0,
#                             'profit_percent': 0
#                         })
#                     if line.move_id.invoice_date >= previous_yr_start.date() and line.move_id.invoice_date <= previous_yr_end.date():
#                         lines.update({
#                             'level': 3,
#                             'prev_qty': prev_qty,
#                             'prev_amount': prev_amount,
#                             'prev_profit': prev_profit,
#                             'prev_profit_percent': prev_profit_percent,
#                         })
#                     else:
#                         lines.update({
#                             'level': 3,
#                             'prev_qty': 0,
#                             'prev_amount': 0,
#                             'prev_profit': 0,
#                             'prev_profit_percent': 0
#                         })
#                     if line.move_id.invoice_date >= last_yr_start.date() and line.move_id.invoice_date <= last_yr_end.date():
#                         lines.update({
#                             'level': 3,
#                             'last_qty': last_qty,
#                             'last_amount': last_amount,
#                             'last_profit': last_profit,
#                             'last_profit_percent': last_profit_percent,
#                         })
#                     else:
#                         lines.update({
#                             'level': 3,
#                             'last_qty': 0,
#                             'last_amount': 0,
#                             'last_profit': 0,
#                             'last_profit_percent': 0
#                         })
#                     data_list.append(lines)
#
#         #     #     sum_sales_amount += sales_amount
#         #     #     sum_quantity += quantity
#         #     #
#         #     # if sum_sales_amount != 0:
#         #     #     data_list.append({
#         #     #         'type': 'amount',
#         #     #         'total_sale': sum_sales_amount,
#         #     #         'total_qty': sum_quantity
#         #     #     })
#         #     # sum_sales_amount = 0
#         #     # sum_quantity = 0
#
#         if not data_list:
#             raise ValidationError(_('No data in this date range'))
#
#         return {
#             'doc_ids': self.ids,
#             'datas': data_list,
#             'doc_model': model,
#             'currency_id': currency_id,
#             'company_id': browsed_company.name,
#             'company_details': browsed_company.company_details,
#             'company_zip': browsed_company.zip,
#             'company_state': browsed_company.state_id.name,
#             'company_country': browsed_company.country_id.name,
#             'from_date': date_from,
#             'to_date': date_end,
#             'last_first_year_start': previous_yr_start,
#             'last_first_year_end': previous_yr_end,
#             'last_second_year_start': last_yr_start,
#             'last_second_year_end': last_yr_end,
#         }
