import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import image_data_uri


class SlowMovingItemReport(models.AbstractModel):
    _name = 'report.kg_ultracare_inventory.slow_moving_item_report_template'
    _description = 'Slow Moving Item Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        company_id = data['form'].get('company_id')
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
        date_end = data['form'].get('date_to', time.strftime('%Y-%m-%d'))
        less_sales_qty = data['form'].get('less_sales_qty')
        browsed_currency_id = data['form'].get('currency_id')
        currency_id = self.env['res.currency'].browse(browsed_currency_id[0])
        browsed_company = self.env['res.company'].browse(company_id[0])

        data = []
        stock_move_id = self.env['stock.move'].search(
            [('date', '>=', date_from), ('date', '<=', date_end), ('state', '=', 'done'),
             ('location_usage', '=', ['internal', 'transit']), ('location_dest_usage', '!=', ['internal', 'transit']),('product_uom_qty','!=',0.00)])
        product = stock_move_id.mapped('product_id')
        for prod in product:
            filter_product = stock_move_id.filtered(lambda x:x.product_id.id == prod.id)
            sum_qty = sum(filter_product.mapped('product_uom_qty'))
            if sum_qty <= less_sales_qty:
                data.append({
                    'item_code':filter_product.product_id.default_code,
                    'description':filter_product.product_id.name,
                })
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
            'from_date': date_from,
            'to_date': date_end
        }
