from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv.expression import expression


class StationaryConsumption(models.Model):
    _name = 'stationary.consumption'
    _description = 'Stationary Consumption'

    def _domain_location_id(self):
        if not self._is_inventory_mode():
            return
        return [('usage', 'in', ['internal', 'transit'])]

    @api.model
    def _is_inventory_mode(self):
        """ Used to control whether a quant was written on or created during an
        "inventory session", meaning a mode where we need to create the stock.move
        record necessary to be consistent with the `inventory_quantity` field.
        """
        return self.env.context.get('inventory_mode') and self.user_has_groups('stock.group_stock_user')

    def _domain_product_id(self):
        if not self._is_inventory_mode():
            return
        domain = [('type', '=', 'product')]
        if self.env.context.get('product_tmpl_ids') or self.env.context.get('product_tmpl_id'):
            products = self.env.context.get('product_tmpl_ids', []) + [self.env.context.get('product_tmpl_id', 0)]
            domain = expression.AND([domain, [('product_tmpl_id', 'in', products)]])
        return domain

    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=lambda self: self._domain_product_id(),
        ondelete='restrict', required=True, index=True, check_company=True)
    product_tmpl_id = fields.Many2one(
        'product.template', string='Product Template',
        related='product_id.product_tmpl_id')
    inventory_quantity = fields.Float(
        'Counted Quantity', digits='Product Unit of Measure',
        help="The product's counted quantity.")
    product_uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        readonly=True, related='product_id.uom_id')
    used_qty = fields.Float(string="Used Quantity", digits='Product Unit of Measure')
    quantity = fields.Float(
        'Quantity',
        help='Quantity of products in this quant, in the default unit of measure of the product',
        readonly=True, digits='Product Unit of Measure')
    inventory_diff_quantity = fields.Float(
        'Difference',
        help="Indicates the gap between the product's theoretical quantity and its counted quantity.",
        digits='Product Unit of Measure')
    inventory_date = fields.Date(
        'Scheduled Date', store=True, readonly=False,
        help="Next date the On Hand Quantity should be counted.")
    user_id = fields.Many2one(
        'res.users', 'Assigned To', help="User assigned to do product count.")
    company_id = fields.Many2one('res.company', string="Company")
    product_categ_id = fields.Many2one(related='product_tmpl_id.categ_id')
    location_id = fields.Many2one(
        'stock.location', 'Location',
        domain=lambda self: self._domain_location_id(),
        auto_join=True, ondelete='restrict', required=True, index=True, check_company=True)
    is_consumed = fields.Boolean(string="Consumed")
    state = fields.Selection([
        ('done', 'Done'),
        ('draft', 'Draft'),
    ], readonly=True, string='State', default='draft')

    @api.onchange('used_qty')
    def onchange_used_qty(self):
        if self.used_qty:
            self.write({'inventory_quantity': self.used_qty})

    @api.onchange('location_id', 'product_id')
    def onchange_onhand_qty_update(self):
        self.quantity = 0
        if self.location_id:
            if self.product_id:
                print(self.location_id)
                quant = self.env['stock.quant'].search(
                    [('location_id', '=', self.location_id.id), ('product_id', '=', self.product_id.id)])
                print(quant)
                self.quantity = sum(quant.mapped('quantity'))

    @api.onchange('inventory_quantity', 'quantity')
    def onchange_inventory_diff_quantity(self):
        # for quant in self:
        if self.product_id:
            if self.inventory_quantity > 0:
                print("KOOOOOOOOOOOOOIIIIIIIIII")
                self.inventory_diff_quantity = self.quantity - self.inventory_quantity

    def action_apply_stationary(self):
        if self.quantity > self.inventory_quantity:
            if self.inventory_quantity > 0:
                loc = self.env['stock.location'].search(
                    [('usage', '=', 'inventory'), ('is_stationary_consumption', '=', True)], limit=1)
                name = _('Stationary Consumption Quantity Updated')
                bb = self.env['stock.move'].create({
                    'name': self.env.context.get('inventory_name') or name,
                    'product_id': self.product_id.id,
                    'product_uom': self.product_uom_id.id,
                    'product_uom_qty': self.inventory_quantity,
                    'company_id': self.company_id.id or self.env.company.id,
                    'state': 'confirmed',
                    'location_id': self.location_id.id,
                    'location_dest_id': loc.id,
                    'is_inventory': True,
                    'move_line_ids': [(0, 0, {
                        'product_id': self.product_id.id,
                        'product_uom_id': self.product_uom_id.id,
                        'qty_done': self.inventory_quantity,
                        'location_id': self.location_id.id,
                        'location_dest_id': loc.id,
                        'consumed': True,
                        'company_id': self.company_id.id or self.env.company.id,
                        'reference': name,
                    })]
                })
                bb._action_done()
                self.is_consumed = True
                self.state = 'done'
        else:
            raise UserError("You have no quantity")

    def action_stationary_history(self):
        print("HAIIII")
        self.ensure_one()
        action = {
            'name': _('History'),
            'view_mode': 'list,form',
            'res_model': 'stock.move.line',
            'views': [(self.env.ref('stock.view_move_line_tree').id, 'list'), (False, 'form')],
            'type': 'ir.actions.act_window',
            'context': {
                'search_default_inventory': 1,
                'search_default_done': 1,
                'search_default_product_id': self.product_id.id,
            },
            'domain': [
                ('consumed', '=', True),
                '|',
                ('location_id', '=', self.location_id.id),
                ('location_dest_id', '=', self.location_id.id),
            ],
        }
        return action
