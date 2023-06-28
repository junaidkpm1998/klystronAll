import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import image_data_uri


class ProductionGoodsReport(models.AbstractModel):
    _name = 'report.kg_ultracare_inventory.production_goods_template_id'
    _description = 'Production Goods Report'

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
        mrp_production_id = self.env['mrp.production'].search(
            [('date_planned_start', '>=', date_from), ('date_planned_start', '<=', date_end), ('state', '=', 'done')])
        for mrp_order in mrp_production_id:
            prod_number = mrp_order.name
            date = mrp_order.date_planned_start.date()

            result = []
            if mrp_order.machine_id.name and mrp_order.machine_id.serial_no:
                result.append((mrp_order.machine_id.name + '/' + mrp_order.machine_id.serial_no))
            if mrp_order.machine_id.name and not mrp_order.machine_id.serial_no:
                result.append((mrp_order.machine_id.name))
            machine = ' '.join([str(elem) for elem in result])

            sales_man = mrp_order.user_id.name
            order_no = mrp_order.origin
            item_code = mrp_order.product_id.default_code
            description = mrp_order.product_id.name
            qty = sum(mrp_order.mapped('move_raw_ids.quantity_done'))
            rate = sum(mrp_order.mapped('move_raw_ids.product_id.standard_price'))
            cost = sum(mrp_order.mapped('move_raw_ids.total_cost'))

            mrp_orders_list = {
                'prod_number': prod_number,
                'date': date,
                'machine': machine,
                'sales_man': sales_man,
                'order_no': order_no,
                'item_code': item_code,
                'description': description,
                'qty': qty,
                'rate': rate,
                'cost': cost,
            }
            data.append(mrp_orders_list)

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
