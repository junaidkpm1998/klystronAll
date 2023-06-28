import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError


class InOutLedgerReport(models.AbstractModel):
    _name = 'report.kg_ultracare_inventory.in_out_ledger_report_template_id'
    _description = 'INOUT Ledger Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        company_id = data['form'].get('company_id')
        year = data['form'].get('year')
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
        date_end = data['form'].get('date_to', time.strftime('%Y-%m-%d'))
        browsed_currency_id = data['form'].get('currency_id')
        currency_id = self.env['res.currency'].browse(browsed_currency_id[0])
        browsed_company = self.env['res.company'].browse(company_id[0])

        data = []
        total_in_qty = 0
        total_out_qty = 0
        balance = 0.00
        balance_amt = 0.00
        product_id = self.env['product.product'].search([])
        for prod in product_id:
            product_list = {'type': 'product', 'product_name': prod.name,
                            'product_code': prod.default_code}
            stock_move_id = self.env['stock.move'].search(
                [('date', '>=', date_from), ('date', '<=', date_end), ('state', '=', 'done'),
                 ('product_id', '=', prod.id)], order='date asc')
            if len(stock_move_id) > 0:
                data.append(product_list)
            if stock_move_id:
                for vals in stock_move_id:
                    doc_date = vals.date.date()
                    doc_no = vals.id
                    reference = vals.reference
                    cost = vals.product_id.standard_price
                    rate = vals.product_id.lst_price
                    picking_type = vals.picking_type_id.name
                    in_qty = 0.00
                    out_qty = 0.00

                    if (vals.location_usage in ('internal', 'transit')) and (
                            vals.location_dest_usage not in ('internal', 'transit')):
                        out_qty = -abs(vals.product_uom_qty)
                    if (vals.location_usage not in ('internal', 'transit')) and (
                            vals.location_dest_usage in ('internal', 'transit')):
                        in_qty = vals.product_uom_qty
                    # opening_product_move_ids = self.env['stock.move'].search(
                    #     [('date', '>=', date_from), ('date', '<=', date_end), ('state', '=', 'done'),
                    #      ('product_id', '=', vals.product_id.id)], order='date asc')
                    # opening_balance_qty = sum(each1.product_uom_qty for each1 in opening_product_move_ids)
                    # opening_balance_amt = sum(
                    #     each1.product_tmpl_id.standard_price for each1 in opening_product_move_ids)
                    # balance = balance + in_qty - out_qty
                    # if opening_balance_qty != 0:
                    #     balance = opening_balance_qty + in_qty - out_qty
                    #     balance_amt = round(opening_balance_qty * opening_balance_amt, 2)
                    balance = in_qty + balance + out_qty
                    balance_amt = balance * cost

                    product_list = {
                        'type': 'data',
                        'doc_date': doc_date,
                        'picking_type': picking_type,
                        'doc_no': doc_no,
                        'reference': reference,
                        'cost': cost,
                        'rate': rate,
                        'in_qty': in_qty,
                        'out_qty': out_qty,
                        'balance': balance,
                        'balance_amt': balance_amt,
                    }
                    data.append(product_list)

                    total_in_qty += in_qty
                    total_out_qty += out_qty

            product_list = {
                'type': 'amount',
                'total_in_qty': total_in_qty,
                'total_out_qty': total_out_qty,
            }
            if total_in_qty or total_out_qty:
                data.append(product_list)
            total_in_qty = 0
            total_out_qty = 0
        print(data)
        if not data:
            raise ValidationError(_('No data in this date range'))

        return {
            'doc_ids': self.ids,
            'datas': data,
            'doc_model': model,
            'currency_id': currency_id,
            'company_id': browsed_company.name,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
            'from_date': date_from,
            'to_date': date_end
        }
