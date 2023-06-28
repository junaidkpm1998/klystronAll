import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError


class ProfitabilityAnalysisReport(models.AbstractModel):
    _name = 'report.kg_ultracare_sale.sales_register_report_template'
    _description = 'Profitability Analysis Report'

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

        account_move_line_id = self.env['account.move.line'].search(
            [('move_id.invoice_date', '>=', date_from), ('move_id.invoice_date', '<=', date_end),
             ('move_id.state', '=', 'posted')])
        sum_quantity = sum(account_move_line_id.mapped('quantity'))

        data = []
        product_id = self.env['product.product'].search([])
        for prod in product_id:
            if prod.name:
                product_name = str(prod.name).upper()
            else:
                product_name = ' '
            if prod.default_code:
                product_code = str(prod.default_code).upper()
            else:
                product_code = ' '
            account_move_line = {'type': 'product',
                                 'product_name': product_name,
                                 'product_code': product_code
                                 }
            account_move_line_id = self.env['account.move.line'].search(
                [('move_id.invoice_date', '>=', date_from), ('move_id.invoice_date', '<=', date_end),
                 ('move_id.state', '=', 'posted'), ('product_id', '=', prod.id), ('move_type', '=', 'out_invoice')])

            if len(account_move_line_id) > 0:
                data.append(account_move_line)
            if account_move_line_id:
                for vals in account_move_line_id:
                    doc_date = vals.invoice_date
                    doc_no = vals.id
                    order_no = vals.sale_line_ids.order_id.name
                    reference = vals.name
                    brand = vals.product_id.product_brand.name
                    quantity = vals.quantity
                    units = vals.product_uom_id.name
                    rate = vals.price_unit
                    currency = vals.currency_id.name
                    amount = vals.price_subtotal
                    amount_bc = vals.currency_id.compute(amount, currency_id)
                    account_move_line = {
                        'type': 'data',
                        'doc_date': doc_date,
                        'doc_no': doc_no,
                        'order_no': order_no,
                        'reference': reference,
                        'brand': brand,
                        'quantity': quantity,
                        'units': units,
                        'rate': rate,
                        'currency': currency,
                        'amount': amount,
                        'amount_bc': amount_bc,
                    }
                    data.append(account_move_line)
        # if not data:
        #     raise ValidationError(_('No data in this date range'))

        return {
            'doc_ids': self.ids,
            'datas': data,
            'sum_quantity': sum_quantity,
            'doc_model': model,
            'currency_id': currency_id.name,
            'company_id': browsed_company.name,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
            'from_date': date_from,
            'to_date': date_end
        }
