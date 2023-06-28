from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    do_grn_description = fields.Text(string="Do/GRN Description")

    @api.model
    def get_users_from_group(self, group_name):
        group = self.env.ref('%s' % group_name)
        users = group.users
        return users

    def button_validate(self):
        users = self.get_users_from_group('stock.group_stock_user')
        print(users, "USERSSSS")
        delivery = self.env['stock.picking.type'].search([('code', '=', 'outgoing'), ('sequence_code', '=', 'OUT')])
        print(self.env.user.has_group('stock.group_stock_user'), "AAA")
        if self.picking_type_id == delivery.id:
            if self.env.user.has_group('stock.group_stock_user') and not self.env.user.has_group(
                    'stock.group_stock_manager'):
                raise UserError(
                    'You do not have permission to validate the delivery order. Please contact your manager.')
            else:
                res = super(StockPicking, self).button_validate()
                return res
        else:
            res = super(StockPicking, self).button_validate()
            return res

    def action_validate_picking(self):
        print(self._context.get('active_ids'), "SELFFF")
        for i in self._context.get('active_ids'):
            print(i, "LLL")
            pick = self.env['stock.picking'].browse(i)
            if pick.state == 'assigned':
                a = pick.button_validate()
                print(a, "AAA")
                if not a == True:
                    raise UserError('Please update done qty manually for validating DO')
                # dem_qty = 0
                # done_qty = 0
                # for k in i.move_line_ids:
                #     dem_qty += k.product_uom_qty
                #     done_qty += k.quantity_done
                # if dem_qty
