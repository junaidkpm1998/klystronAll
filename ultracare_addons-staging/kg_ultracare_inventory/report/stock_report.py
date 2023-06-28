import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError


class InOutLedgerReport(models.AbstractModel):
    _name = 'report.kg_ultracare_inventory.kg_stock_report_template_id'
    _description = 'Stock Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        company_id = data['form'].get('company_id')
        browsed_currency_id = data['form'].get('currency_id')
        currency_id = self.env['res.currency'].browse(browsed_currency_id[0])
        browsed_company = self.env['res.company'].browse(company_id[0])
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
        data = []
        stock_id = self.env['product.product'].search(
            [('stock_quant_ids.create_date', '>=', date_from), ('qty_available', '!=', 0.00)])
        for stock_val in stock_id:
            item_code = stock_val.default_code
            description = stock_val.name
            unit = stock_val.uom_name
            qty = stock_val.qty_available

            product = {
                'item_code': item_code,
                'product_name': description,
                'unit': unit,
                'qty': qty,
            }
            data.append(product)

        # if not data:
        #     raise ValidationError(_('No data in this date range'))

        return {
            'doc_ids': self.ids,
            'datas': data,
            'date_from': date_from,
            'doc_model': model,
            'currency_id': currency_id,
            'company_id': browsed_company.name,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
        }
