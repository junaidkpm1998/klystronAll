import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import image_data_uri


class CustomerAnalysisReport(models.AbstractModel):
    _name = 'report.kg_ultracare_sale.sale_analysis_report_template'
    _description = 'Sale Analysis Report'

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

        partner_id = self.env['res.partner'].search([])
        data_list = []
        sum_sales_amount = 0
        sum_quantity = 0
        for customer in partner_id:
            account_line = self.env['account.move.line'].search(
                [('move_id.invoice_date', '>=', date_from), ('move_id.invoice_date', '<=', date_end),
                 ('move_id.state', '=', 'posted'), ('move_id.partner_id', '=', customer.id),
                 ('move_id.move_type', '=', 'out_invoice')], order='product_id asc')

            customer_name = str(customer.name).upper()
            customer_code = str(customer.customer_code).upper()
            account_move_line = {'type': 'customer',
                                 'customer_name': customer_name,
                                 'customer_code': customer_code,
                                 }
            if len(account_line) > 0:
                data_list.append(account_move_line)

            if len(account_line) > 0:
                product = account_line[0].product_id.id
                inr = 0
                sales_amount = 0
                quantity = 0
                while (inr < len(account_line)):
                    if account_line[inr].product_id.id == product:
                        sales_amount += account_line[inr].price_subtotal
                        quantity += account_line[inr].quantity
                    else:
                        rtn_line = self.env['account.move.line'].search(
                            [('move_id.invoice_date', '<=', date_end), ('move_id.invoice_date', '>=', date_from),
                             ('move_id.state', '=', 'posted'),
                             ('product_id', '=', product), ('move_id.move_type', '=', 'out_invoice')])
                        vart = []
                        if rtn_line.product_id.product_template_variant_value_ids:
                            for var in rtn_line.product_id.product_template_variant_value_ids:
                                vart.append(var.name)
                        variance = ','.join([str(elem) for elem in vart])
                        sale_date = rtn_line[0].sale_line_ids.order_id.date_order

                        data_list.append(
                            {
                                'type': 'data',
                                'product_category_code': str(
                                    account_line[inr - 1].product_id.categ_id.parent_id.name).upper(),
                                'product_category': str(account_line[inr - 1].product_id.categ_id.name).upper(),
                                'product_group_code': str(account_line[inr - 1].product_id.product_group.code).upper(),
                                'product_group': str(account_line[inr - 1].product_id.product_group.name).upper(),
                                'product_code': str(account_line[inr - 1].product_id.default_code).upper(),
                                'product_name': str(account_line[inr - 1].product_id.name).upper(),
                                'sales_amount': sales_amount,
                                'quantity': quantity,
                                'variance': variance,
                                'sale_date': sale_date,
                            })
                        sum_sales_amount += sales_amount
                        sum_quantity += quantity

                        product = account_line[inr].product_id.id
                        sales_amount = 0
                        quantity = 0
                        sales_amount += account_line[inr].price_subtotal
                        quantity += account_line[inr].quantity
                    inr += 1

                rtn_line = self.env['account.move.line'].search(
                    [('move_id.invoice_date', '<=', date_end), ('move_id.invoice_date', '>=', date_from),
                     ('move_id.state', '=', 'posted'), ('product_id', '=', account_line[inr - 1].product_id.id),
                     ('move_id.move_type', '=', 'out_invoice')])
                vart = []
                if rtn_line.product_id.product_template_variant_value_ids:
                    for var in rtn_line.product_id.product_template_variant_value_ids:
                        vart.append(var.name)
                variance = ','.join([str(elem) for elem in vart])
                sale_date = rtn_line[0].sale_line_ids.order_id.date_order
                data_list.append(
                    {
                        'type': 'data',
                        'product_category_code': str(account_line[inr - 1].product_id.categ_id.parent_id.name).upper(),
                        'product_category': str(account_line[inr - 1].product_id.categ_id.name).upper(),
                        'product_group_code': str(account_line[inr - 1].product_id.product_group.code).upper(),
                        'product_group': str(account_line[inr - 1].product_id.product_group.name).upper(),
                        'product_code': str(account_line[inr - 1].product_id.default_code).upper(),
                        'product_name': str(account_line[inr - 1].product_id.name).upper(),
                        'sales_amount': sales_amount,
                        'quantity': quantity,
                        'variance': variance,
                        'sale_date': sale_date,
                    })

                sum_sales_amount += sales_amount
                sum_quantity += quantity

            if sum_sales_amount != 0:
                data_list.append({
                    'type': 'amount',
                    'total_sale': sum_sales_amount,
                    'total_qty': sum_quantity
                })
            sum_sales_amount = 0
            sum_quantity = 0

        # if not data_list:
        #     raise ValidationError(_('No data in this date range'))

        return {
            'doc_ids': self.ids,
            'datas': data_list,
            'doc_model': model,
            'currency_id': currency_id,
            'company_id': browsed_company.name,
            'company_details': browsed_company.company_details,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
            'from_date': date_from,
            'to_date': date_end,
        }
