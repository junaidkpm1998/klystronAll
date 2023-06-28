import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import image_data_uri, groupby


class StockAdjustmentRegisterReport(models.AbstractModel):
    _name = 'report.kg_ultracare_inventory.stock_adjustment_template_id'
    _description = 'Stock Adjustment Register Report'

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
        stock_quant_id = self.env['stock.quant'].search(
            [('inventory_date', '>=', date_from), ('inventory_date', '<=', date_end),
             ('location_id.usage', 'in', ['internal', 'transit'])])

        if stock_quant_id:
            for stock_adj in stock_quant_id:
                result = []
                if stock_adj.location_id.name and stock_adj.location_id.location_id.name:
                    result.append((stock_adj.location_id.location_id.name + '/' + stock_adj.location_id.name))
                if stock_adj.location_id.name and not stock_adj.location_id.location_id.name:
                    result.append((stock_adj.location_id.name))
                to_location = ' '.join([str(elem) for elem in result])

                item_code = stock_adj.product_id.default_code
                description = stock_adj.product_id.name
                unit = stock_adj.product_uom_id.name
                qty = stock_adj.quantity

                stock_adjustment = {
                    'type': 'stock',
                    'to_location': to_location,
                    'item_code': item_code,
                    'description': description,
                    'unit': unit,
                    'qty': qty,
                }
                data.append(stock_adjustment)

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
            'logo': browsed_company.logo and image_data_uri(browsed_company.logo),
            'from_date': date_from,
            'to_date': date_end
        }
