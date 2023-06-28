import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import image_data_uri, groupby


class StockLedgerreport(models.AbstractModel):
    _name = 'report.kg_ultracare_inventory.stock_ledger_template_id'
    _description = 'Stock Ledger Report'

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

        product_category = self.env['product.category'].search([])
        data_list = []
        for prod_cate in product_category:
            stock_move_line_id = self.env['stock.move.line'].search(
                [('date', '>=', date_from), ('date', '<=', date_end), ('state', '=', 'done'),
                 ('product_id.categ_id', '=', prod_cate.id)], order='product_id asc')

            category_list = {
                'type': 'category',
                'product_category_code': str(prod_cate.name).upper(),
                'product_category_name': str(prod_cate.parent_id.name).upper(),
            }
            if len(stock_move_line_id) > 0:
                data_list.append(category_list)

            if len(stock_move_line_id) > 0:
                product = stock_move_line_id[0].product_id.id
                inr = 0
                mrp = 0
                issues = 0
                purchase_return = 0
                sales_return = 0
                cl_stock = 0
                inventory_adj = 0
                while (inr < len(stock_move_line_id)):
                    if stock_move_line_id[inr].product_id.id == product:
                        mrp += stock_move_line_id[inr].production_id.product_qty

                        if (stock_move_line_id[inr].move_id.location_usage in ('internal', 'transit')) and (
                                stock_move_line_id[inr].move_id.location_dest_usage not in ('internal', 'transit')):
                            issues += stock_move_line_id[inr].qty_done

                        if (stock_move_line_id[inr].picking_type_id.warehouse_id.out_type_id) and (
                                stock_move_line_id[inr].location_usage in ('internal', 'transit')) and (
                                stock_move_line_id[inr].location_dest_usage not in ('internal', 'transit')):
                            purchase_return += stock_move_line_id[inr].qty_done

                        if (stock_move_line_id[inr].picking_type_id.warehouse_id.return_type_id) and (
                                stock_move_line_id[inr].location_usage not in ('internal', 'transit')) and (
                                stock_move_line_id[inr].location_dest_usage in ('internal', 'transit')):
                            sales_return += stock_move_line_id[inr].qty_done

                        cl_stock += stock_move_line_id[inr].product_id.qty_available

                        inventory_adj_id = self.env['stock.quant'].search(
                            [('product_id', '=', stock_move_line_id[inr].product_id.id),
                             ('location_id.usage', 'in', ['internal', 'transit'])])
                        inventory_adj += sum(inventory_adj_id.mapped('quantity'))

                    else:
                        rtn_line = self.env['stock.move.line'].search(
                            [('date', '>=', date_from), ('date', '<=', date_end), ('state', '=', 'done'),
                             ('product_id', '=', product)])
                        data_list.append(
                            {
                                'type': 'data',
                                'item_code': stock_move_line_id[inr].product_id.default_code,
                                'product_name': stock_move_line_id[inr].product_id.name,
                                'opening': stock_move_line_id[inr].product_id.with_context(
                                    {'to_date': date_from}).qty_available,
                                'mrp': mrp,
                                'lotr': stock_move_line_id[inr].lot_id.name,
                                'issues': issues,
                                'purchase_return': purchase_return,
                                'sales_return': sales_return,
                                'cl_stock': cl_stock,
                                'inventory_adj': inventory_adj,
                            })

                        product = stock_move_line_id[inr].product_id.id
                        mrp = 0
                        issues = 0
                        purchase_return = 0
                        sales_return = 0
                        cl_stock = 0
                        inventory_adj = 0

                        mrp += stock_move_line_id[inr].production_id.product_qty

                        if (stock_move_line_id[inr].move_id.location_usage in ('internal', 'transit')) and (
                                stock_move_line_id[inr].move_id.location_dest_usage not in ('internal', 'transit')):
                            issues += stock_move_line_id[inr].qty_done

                        if (stock_move_line_id[inr].picking_type_id.warehouse_id.out_type_id) and (
                                stock_move_line_id[inr].location_usage in ('internal', 'transit')) and (
                                stock_move_line_id[inr].location_dest_usage not in ('internal', 'transit')):
                            purchase_return += stock_move_line_id[inr].qty_done

                        if (stock_move_line_id[inr].picking_type_id.warehouse_id.return_type_id) and (
                                stock_move_line_id[inr].location_usage not in ('internal', 'transit')) and (
                                stock_move_line_id[inr].location_dest_usage in ('internal', 'transit')):
                            sales_return += stock_move_line_id[inr].qty_done

                        cl_stock += stock_move_line_id[inr].product_id.qty_available

                        inventory_adj_id = self.env['stock.quant'].search(
                            [('product_id', '=', stock_move_line_id[inr].product_id.id),
                             ('location_id.usage', 'in', ['internal', 'transit'])])
                        inventory_adj += sum(inventory_adj_id.mapped('quantity'))
                    inr += 1

                rtn_line = self.env['stock.move.line'].search(
                    [('date', '>=', date_from), ('date', '<=', date_end), ('state', '=', 'done'),
                     ('product_id', '=', stock_move_line_id[inr - 1].product_id.id),
                     ])

                data_list.append(
                    {
                        'type': 'data',
                        'item_code': stock_move_line_id[inr - 1].product_id.default_code,
                        'product_name': stock_move_line_id[inr - 1].product_id.name,
                        'opening': stock_move_line_id[inr - 1].product_id.with_context(
                            {'to_date': date_from}).qty_available,
                        'mrp': mrp,
                        'lotr': stock_move_line_id[inr - 1].lot_id.name,
                        'issues': issues,
                        'purchase_return': purchase_return,
                        'sales_return': sales_return,
                        'cl_stock': cl_stock,
                        'inventory_adj': inventory_adj,
                    })
        # if not data_list:
        #     raise ValidationError(_('No data in this date range'))

        return {
            'doc_ids': self.ids,
            'datas': data_list,
            'doc_model': model,
            'currency_id': currency_id,
            'company_id': browsed_company.name,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
            'from_date': date_from,
            'to_date': date_end
        }

        # data = []
        # product_category = self.env['product.category'].search([])
        # for prod_cate in product_category:
        #     category_list = {
        #         'type': 'category',
        #         'product_category_code': str(prod_cate.name).upper(),
        #         'product_category_name': str(prod_cate.parent_id.name).upper(),
        #     }
        #     stock_move_line_id = self.env['stock.move.line'].search(
        #         [('date', '>=', date_from), ('date', '<=', date_end), ('state', '=', 'done'),
        #          ('product_id.categ_id', '=', prod_cate.id)], order='product_id asc')
        #     if len(stock_move_line_id) > 0:
        #         data.append(category_list)
        #     for vals in stock_move_line_id:
        #         item_code = vals.product_id.default_code
        #         product_name = vals.product_id.name
        #         opening = vals.product_id.with_context({'to_date': date_end}, {'to_date': date_from}).qty_available
        #         mrp = vals.production_id.product_qty
        #         lotr = vals.lot_id.name
        #         cl_stock = vals.product_id.qty_available
        #
        #         inventory_adj_id = self.env['stock.quant'].search(
        #             [('product_id', '=', vals.product_id.id), ('location_id.usage', 'in', ['internal', 'transit'])])
        #         print(inventory_adj_id)
        #         inventory_adj = sum(inventory_adj_id.mapped('quantity'))
        #
        #         issues = ''
        #         if (vals.move_id.location_usage in ('internal', 'transit')) and (
        #                 vals.move_id.location_dest_usage not in ('internal', 'transit')):
        #             issues = vals.qty_done
        #
        #         purchase_return = ''
        #         if (vals.picking_type_id.warehouse_id.return_type_id) and (
        #                 vals.location_usage in ('internal', 'transit')) and (
        #                 vals.location_dest_usage not in ('internal', 'transit')):
        #             purchase_return = vals.qty_done
        #
        #         sales_return = ''
        #         if (vals.picking_type_id.warehouse_id.return_type_id) and (
        #                 vals.location_usage not in ('internal', 'transit')) and (
        #                 vals.location_dest_usage in ('internal', 'transit')):
        #             sales_return = vals.qty_done
        #
        #         category_list = {
        #             'type': 'data',
        #             'item_code': item_code,
        #             'product_name': product_name,
        #             'opening': opening,
        #             'mrp': mrp,
        #             'lotr': lotr,
        #             'issues': issues,
        #             'purchase_return': purchase_return,
        #             'sales_return': sales_return,
        #             'cl_stock': cl_stock,
        #             'inventory_adj': inventory_adj,
        #         }
        #         data.append(category_list)
        #
        # if not data:
        #     raise ValidationError(_('No data in this date range'))
