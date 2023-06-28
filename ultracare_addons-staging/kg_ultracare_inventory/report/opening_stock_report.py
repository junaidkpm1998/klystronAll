import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError


class OpeningStockReport(models.AbstractModel):
    _name = 'report.kg_ultracare_inventory.opening_stock_report_template_id'
    _description = 'Opening Stock Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        company_id = data['form'].get('company_id')
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
        browsed_currency_id = data['form'].get('currency_id')
        currency_id = self.env['res.currency'].browse(browsed_currency_id[0])
        browsed_company = self.env['res.company'].browse(company_id[0])

        data = []
        product = self.env['product.product'].search([])
        for prod in product:
            open_qty = prod.with_context({'to_date': date_from}).qty_available
            product_name = prod.with_context({'to_date': date_from}).name
            item_code = prod.with_context({'to_date': date_from}).default_code
            cost = prod.with_context({'to_date': date_from}).standard_price
            cost_value = prod.with_context({'to_date': date_from}).lst_price
            unit = prod.with_context({'to_date': date_from}).uom_name

            if open_qty:
                product = {
                    'item_code': item_code,
                    'product_name': product_name,
                    'unit': unit,
                    'qty': open_qty,
                    'cost': cost,
                    'cost_value': cost_value,
                }
                data.append(product)

        # if not data:
        #     raise ValidationError(_('No data in this date range'))

        return {
            'doc_ids': self.ids,
            'datas': data,
            'doc_model': model,
            'currency_id': currency_id,
            'company_id': browsed_company.name,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
            'from_date': date_from
        }