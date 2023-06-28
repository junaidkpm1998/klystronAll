from datetime import date

from odoo import models, fields, api, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    kg_sf_line = fields.Many2one('kg.sales.forecast')
    expected_delivery = fields.Datetime('Expected Delivery', compute='compute_expected_date')

    @api.onchange('customer_lead')
    def compute_expected_date(self):
        for i in self:
            i.expected_delivery = i._expected_date()

    def action_open_sales_forecast(self):
        return {
            'name': 'Sales Forecast',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'kg.sales.forecast',
            'domain': [('sale_ids', 'in', self.ids)],
            # 'target': 'current'
        }

    def action_create_sf(self):
        data = []
        self._context.get('active_ids')
        not_lines = []
        for i in self._context.get('active_ids'):
            # sale_line = self.env['sale.order.line'].browse(i)

            forecast = self.env['kg.sf.lines'].search([('sale_line_id', '=', i)])
            if not forecast:
                not_lines.append(i)

        department = self.env['hr.department'].search([('name', '=', 'Sales')])
        if department:
            department = department[0].id

        period = self.env['kg.period'].search([])
        if period:
            period = period[0].id

        for k in not_lines:
            sale_line = self.env['sale.order.line'].browse(k)
            data.append((0, 0, {
                'kg_product_id': sale_line.product_id.id,
                'kg_uom_id': sale_line.product_uom.id,
                'kg_qty': sale_line.product_uom_qty,
                'sale_id': sale_line.order_id.id,
                'sale_line_id': sale_line.id,
            }))
        if data:
            for_cast = self.env['kg.sales.forecast'].search(
                [('kg_state', '=', 'new')], limit=1).sorted('kg_date')
            if not for_cast:
                new = self.env['kg.sales.forecast'].create({'kg_period': period,
                                                            'kg_user_id': self.env.user.id,
                                                            'kg_dep': department,
                                                            'kg_date': date.today(),
                                                            # 'sale_ids': [(6, 0, .order_id.ids)],
                                                            'kg_lines': data})
                for i in new.kg_lines:
                    if i.sale_line_id:
                        i.sale_line_id.kg_sf_line = new.id
            else:
                for_cast.write({'kg_lines': data})
