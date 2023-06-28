# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError


class kg_product_transfer(models.Model):
    _name = 'kg.product.transfer'
    _description = 'Product Transfer'

    name = fields.Char('Name', required=True, default='/')
    state = fields.Selection([('new', 'New'), ('done', 'Done')], default='new', string='Status')

    date = fields.Date('Date', default=fields.Datetime.now)
    transfer_line = fields.One2many('kg.product.transfer.line', 'transfer_id', string="Transfer Line")

    source_location_id = fields.Many2one('stock.location', 'Source Location')
    kg_finish = fields.Boolean(string='Finished Good Conversion', default=False)

    @api.model
    def create(self, vals):
        context = self.env.context
        vals['name'] = self.env['ir.sequence'].next_by_code('kg.product.transfer') or _('New')
        if context.get('store'):
            vals['source_location_id'] = 15
        else:
            vals['source_location_id'] = 19
        result = super(kg_product_transfer, self).create(vals)
        return result

    def get_id_from_param(self, param):
        parameter_obj = self.env['ir.config_parameter']
        key = [('key', '=', param)]
        param_obj = parameter_obj.search(key)
        if not param_obj:
            raise UserError(_('NoParameter Not defined\nconfig it in System Parameters with %s') % param)
        result_id = param_obj.value
        return int(result_id)

    def confirm_transfer(self):

        if self.state != 'new':
            raise UserError(_('it is already in done state'))
        source_location_id = False
        context = self.env.context
        if context.get('store'):
            source_location_id = 15
        else:
            source_location_id = 19
        lines = self.transfer_line
        ##outing
        for line in lines:
            dest_move_lines = []
            src_move_lines = []
            total_quantity_in_location = 0
            total_inventory_value = 0
            unit_price = 0
            out_product_id = line.out_product_id and line.out_product_id.id or False
            quants = self.env['stock.quant'].search(
                [('product_id', '=', out_product_id), ('location_id', '=', source_location_id)])
            if len(quants) < 1:
                raise UserError(_('this product not found in the location'))
            for q in quants:
                total_quantity_in_location = total_quantity_in_location + q.qty
                total_inventory_value = total_inventory_value + q.inventory_value

            if total_quantity_in_location < line.qty:
                raise UserError(_('the available quantity: "%s",location:"%s"') %
                                (total_quantity_in_location, self.source_location_id.name))
            if total_inventory_value <= 0:
                unit_price = 0
            else:

                unit_price = float(total_inventory_value) / float(total_quantity_in_location)
            product_id = line.out_product_id and line.out_product_id.id
            uom_id = line.out_product_id and line.out_product_id.uom_id and line.out_product_id.uom_id.id or False
            price_unit = unit_price
            move = {'name': self.name, 'product_id': product_id, 'product_uom_qty': line.qty, 'product_uom': uom_id,
                    'price_unit': price_unit}
            dest_move_lines.append((0, 0, move))
            picking_obj = self.env['stock.picking']
            picking_type_id = self.get_id_from_param("outing_manually_picking_type")
            picking_type = self.env['stock.picking.type'].browse(picking_type_id)
            dest_picking = picking_obj.create({
                'move_lines': dest_move_lines,
                # 'partner_id':self.env.user.partner_id.id,
                'picking_type_id': picking_type_id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
            })
            dest_picking.action_confirm()
            dest_picking.action_assign()
            dest_picking.action_done()
            line.out_product_id_picking_id = dest_picking.id
            ##in process

            src_move = {'name': self.name, 'product_id': line.in_product_id and line.in_product_id.id,
                        'product_uom_qty': line.qty, 'product_uom': line.in_product_id.uom_id.id,
                        'price_unit': price_unit}
            src_move_lines.append((0, 0, src_move))
            picking_obj = self.env['stock.picking']
            picking_source_type_id = self.get_id_from_param("in_manually_picking_type")
            picking_source_type = self.env['stock.picking.type'].browse(picking_source_type_id)

            source_picking = picking_obj.create({
                'move_lines': src_move_lines,
                # 'partner_id':self.env.user.partner_id.id,
                'picking_type_id': picking_source_type_id,
                'location_id': picking_source_type.default_location_src_id.id,
                'location_dest_id': picking_source_type.default_location_dest_id.id,
            })
            source_picking.action_confirm()
            source_picking.action_assign()
            source_picking.action_done()
            line.in_product_picking_id = source_picking.id

        self.state = 'done'

        return True


class kg_product_transfer_line(models.Model):
    _name = 'kg.product.transfer.line'
    _description = 'Product Transfer Line'

    out_product_id = fields.Many2one('product.product', string="Out Product")
    in_product_id = fields.Many2one('product.product', string="In Product")
    qty = fields.Float(string="Qty")

    in_product_picking_id = fields.Many2one('stock.picking', string="Transfer Doc(in)")
    out_product_id_picking_id = fields.Many2one('stock.picking', string="Transfer Doc(out)")

    transfer_id = fields.Many2one('kg.product.transfer', string="Trnasfer")