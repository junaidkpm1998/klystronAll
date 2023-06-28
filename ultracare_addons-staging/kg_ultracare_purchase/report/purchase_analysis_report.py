import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_repr, image_data_uri


class PurchaseAnalysisReport(models.AbstractModel):
    _name = 'report.kg_ultracare_purchase.purchase_analysis_report_template'
    _description = 'Purchase Analysis Report'

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

        data = []
        partner_id = self.env['res.partner'].search([])
        sum_purchase_amount = 0
        sum_quantity = 0

        for customer in partner_id:
            account_move_line_id = self.env['account.move.line'].search(
                [('move_id.invoice_date', '>=', date_from), ('move_id.invoice_date', '<=', date_end),
                 ('move_id.state', '=', 'posted'), ('move_id.partner_id', '=', customer.id),('move_id.move_type','=','in_invoice')])

            customer_name = str(customer.name).upper()
            customer_code = str(customer.customer_code).upper()
            account_move_line = {'type': 'customer',
                                 'customer_name': customer_name,
                                 'customer_code': customer_code,
                                 }
            if len(account_move_line_id) > 0:
                data.append(account_move_line)

            for vals in account_move_line_id:
                product_category_name = vals.product_id.categ_id.name
                product_category_code = vals.product_id.categ_id.parent_id.name
                product_group = vals.product_id.product_group.name
                product_group_code = vals.product_id.product_group.code
                product_code = vals.product_id.default_code
                product_name = vals.product_id.name
                purchase_amount = vals.price_subtotal
                quantity = vals.quantity
                purchase_date = vals[0].purchase_order_id.date_approve

                account_move_line = {
                    'type': 'data',
                    'product_category': str(product_category_name).upper(),
                    'product_code': str(product_code).upper(),
                    'product_name': str(product_name).upper(),
                    'product_category_code': str(product_category_code).upper(),
                    'purchase_amount': purchase_amount,
                    'quantity': quantity,
                    'purchase_date': purchase_date,
                    'product_group': str(product_group).upper(),
                    'product_group_code': str(product_group_code).upper(),
                }
                data.append(account_move_line)

                sum_purchase_amount += purchase_amount
                sum_quantity += quantity
            account_move_line = {'type': 'amount',
                                 'total_purchase': sum_purchase_amount,
                                 'total_qty': sum_quantity
                                 }
            if sum_purchase_amount != 0:
                data.append(account_move_line)
            sum_purchase_amount = 0
            sum_quantity = 0

        if not data:
            raise ValidationError(_('No data in this date range'))

        return {
            'doc_ids': self.ids,
            'datas': data,
            'doc_model': model,
            'currency_id': currency_id,
            'company_id': browsed_company.name,
            'logo': browsed_company.logo and image_data_uri(browsed_company.logo),
            'company_details': browsed_company.company_details,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
            'from_date': date_from,
            'to_date': date_end,
        }


