# -*- coding: utf-8 -*-
import datetime

import pytz

from odoo import models, api, fields, _, Command
from odoo.exceptions import UserError, ValidationError
from copy import copy

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    already_bom_created_product_ids = fields.Many2many('product.template', 'product_tmpl_id', 'bom_id',
                                                       string="Already Bom Created Product")
    inner_outer_pack_conf = fields.Char(string='Inner * Outer Packing Configuration')
    outer_pack_uom = fields.Char(string='Outer Pack/UOM')
    weight = fields.Float(string='Weight')

    def bom_created(self):
        self.product_tmpl_id.is_it_bom_created = True

    # @api.onchange('product_tmpl_id')
    # def onchange_product_tmpl_id(self):
    #     if self.product_tmpl_id:
    #         self.product_uom_id = self.product_tmpl_id.uom_id.id
    #
    #         self.code = self.product_tmpl_id.default_code
    #         self.outer_pack_uom = self.product_tmpl_id.outer_pack_uom
    #         self.inner_outer_pack_conf = self.product_tmpl_id.inner_outer_pack_conf
    #         self.weight = self.product_tmpl_id.weight_roll or self.product_tmpl_id.defined_weight or self.product_tmpl_id.tn_weight
    #
    #         if self.product_id.product_tmpl_id != self.product_tmpl_id:
    #             self.product_id = False
    #         b = []
    #         for i in self.product_tmpl_id.kg_product_raw_lines:
    #             a = {}
    #             a['product_id'] = i.product_id.id
    #             a['product_uom_id'] = i.product_id.uom_id.id
    #             a['product_qty'] = 1
    #             c = (0, 0, a)
    #             b.append(c)
    #         self.bom_line_ids = b

    @api.model
    def default_get(self, fields):
        res = super(MrpBom, self).default_get(fields)
        product_ids = []
        product_ids_with_bom = self.env['mrp.bom'].search([])
        for bom in product_ids_with_bom:
            product_ids.append(bom.product_tmpl_id and bom.product_tmpl_id.id)
        res['already_bom_created_product_ids'] = [(6, 0, product_ids)]
        return res

    def update_product_master(self):
        bom_line_ids = self.bom_line_ids
        b = []
        current_raw_lines_in_product = self.product_tmpl_id and self.product_tmpl_id.kg_product_raw_lines
        for l in current_raw_lines_in_product:
            l.unlink()
        for line in bom_line_ids:
            a = {}
            a['product_id'] = line.product_id and line.product_id.id or False
            c = (0, 0, a)
            b.append(c)
        self.product_tmpl_id.kg_product_raw_lines = b


class kg_mrp_consumption_warning(models.TransientModel):
    _inherit = "mrp.consumption.warning"

    def action_confirm(self):
        res = super(kg_mrp_consumption_warning, self).action_confirm()
        return res


class mrp_production(models.Model):
    _inherit = "mrp.production"

    kg_shift_id = fields.Many2one('shift.master', string="Shift", required=True)
    shift_master_id = fields.Many2one('shift.master', string="Shift Master")
    kg_day = fields.Char('Day')
    abnormal_wastage_id = fields.One2many('abnormal.wastage.line', 'mrp_id', string="Abnormal Wastage")
    production_planning_id = fields.Many2one('production.planning', string="Production Planning")
    sales_forecast_id = fields.Many2one('kg.sales.forecast', "Sales Forecast")
    kg_lot_producing_id = fields.Char('Lot Serial Number')
    is_jumbo = fields.Boolean('Is Jumbo', default=False)

    ## For creating Material Request ##
    def create_mr(self):
        kg_mrp_id = self.id
        kg_req_date = self.date_planned_start
        line = self.move_raw_ids
        line_vals_array = []
        for li in line:
            vals = (0, 0, {'kg_product': li.product_id and li.product_id.id,
                           'kg_uom': li.product_uom and li.product_uom.id,
                           'kg_qty': li.product_uom_qty,
                           'kg_req_date': kg_req_date})
            line_vals_array.append(vals)
        self.env['kg.mat.req'].create({'kg_mrp_id': kg_mrp_id, 'kg_mat_req_lines': line_vals_array})

    ## total amount calculation of overhead values ##
    @api.depends('kg_overhead_line.amount', 'kg_overhead_line.kg_cost')
    def _compute_overhead_total(self):
        tot = 0
        kg_overhead_line = self.kg_overhead_line
        for line in kg_overhead_line:
            tot = tot + line.amount

        self.kg_overhead_total = tot

    ## For adding Jumbo roll ##
    def action_confirm(self):
        if not self.move_raw_ids:
            raise UserError("Please Select Raw Material Under Components")
        if self.move_raw_ids:
            rec = self.move_raw_ids.filtered(lambda m: m.jumbo_roll == True)
            if not rec:
                raise UserError("Please Select Jumbo Roll Enable Products Under Components")
        return super(mrp_production, self).action_confirm()

    ## For Generating lot or serial code for main product ##
    def action_generate_serial(self):
        # if not any(rec.jumbo_roll and rec.lot_ids for rec in self.move_raw_ids):
        #     raise ValidationError(_('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'))
        rec = self.move_raw_ids.filtered(lambda m: m.jumbo_roll == True)
        if not rec:
            raise UserError("Please Select Jumbo Roll Enable Products Under Components")
        rec = rec[0]
        if rec.jumbo_roll and rec.lot_ids:
            move_line = self.env['stock.move.line'].search(
                [('product_id', '=', rec.product_id.id), ('move_id', '=', rec.id)], limit=1,
                order='create_date desc')

            current_date = datetime.date.today()
            today_date = current_date.strftime("%d%m%Y")

            current_datetime = datetime.datetime.now()
            current_time = current_datetime.strftime("%H-%M")
            # if move_line and not move_line.lot_id:
            #     raise UserError("No Lot allocated for the jumbo roll")

            shift = self.kg_shift_id.name
            vendor_code = move_line.lot_id.kg_picking_id.partner_id.vendor_code
            if vendor_code:
                self.kg_lot_producing_id = f"{today_date}/{current_time}/{shift}/{vendor_code}"
            else:
                self.kg_lot_producing_id = f"{today_date}/{current_time}/{shift}"

            self.lot_producing_id = self.env['stock.lot'].create({
                'product_id': self.product_id.id,
                'company_id': self.company_id.id,
                'name': self.kg_lot_producing_id
            })

            if self.move_finished_ids.filtered(lambda m: m.product_id == self.product_id).move_line_ids:
                self.move_finished_ids.filtered(
                    lambda m: m.product_id == self.product_id).move_line_ids.lot_id = self.lot_producing_id
            # if self.product_id.tracking == 'serial':
            # self._set_qty_producing()

    # def _set_qty_producing(self):
    #     res = super(mrp_production, self)._set_qty_producing()
    #     return res

    @api.model
    def _default_prod_lines(self):
        #        cat_ids =self.env['kg.category'].search([])
        b = []
        print("::::::::::::::")
        misc_id = self.env['product.product'].search([('name', '=', 'Misc Cost')])
        if misc_id:
            a = {}
            a['kg_product'] = misc_id.id
            a['kg_cost'] = 0.25
            c = (0, 0, a)
            b.append(c)
        misc_id = self.env['product.product'].search([('name', '=', 'Exegenecies')])
        if misc_id:
            a = {}
            a['kg_product'] = misc_id.id
            a['kg_cost'] = 0.2
            c = (0, 0, a)
            b.append(c)
        return b

    kg_acc_list = fields.One2many('kg.mrp.account.lines', 'kg_mrp_id')
    kg_overhead_line = fields.One2many('kg.prod.cost', 'kg_mrp_id', 'Product Cost List',
                                       default=lambda self: self._default_prod_lines())

    kg_overhead_total = fields.Float('Overhead Total', compute="_compute_overhead_total", store=True)

    # @RRM  overriding function to calculate finshed product unit cost
    def post_inventory(self):
        moves_to_do = self.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
        for order in self:
            rawmaterial_moveids = []
            total_rawmaterial_cost = 0
            for rawmaterial in order.move_raw_ids:
                rawmaterial_moveids.append(rawmaterial.id)
            rawmaterials = self.env['stock.move'].browse(rawmaterial_moveids)
            for line in rawmaterials:
                default_uom = line.product_id and line.product_id.uom_id
                ###since rawmaterial price unit/cost in move line is based on the default uom mentioned in the product master
                ####in odoo if you purchased in any unit the final cost of each single piece will be based on product master uom

                #####if you directly multiply with qty_done it will be wrong
                ####so converted in to default uom qty
                actual_qty_done_default_uom = line.product_uom._compute_quantity(line.quantity_done, default_uom)

                ##############i got unit price in default uom(by default u will get) based and qunatity also I converted to default uom
                ####now cost will be fine
                line_cost = line.price_unit * actual_qty_done_default_uom
                total_rawmaterial_cost = total_rawmaterial_cost + (line_cost)

            order._cal_price(moves_to_do)
            moves_to_finish = order.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            qty_done = moves_to_finish.quantity_done
            uom_type = moves_to_finish.product_uom.uom_type

            default_uom = moves_to_finish.product_id and moves_to_finish.product_id.uom_id

            ### to restrict final product to be pro
            # if default_uom.id != moves_to_finish.product_uom.id:
            #     raise UserError('the finshed product UOM should be same as its default uom mentioned i n product master' % moves_to_finish.product_uom.name)

            total_overhead_cost = self.kg_overhead_total or 0
            total_cost = total_rawmaterial_cost + total_overhead_cost
            if qty_done:
                unit_cost = float(total_cost) / float(qty_done)
                moves_to_finish.write({'price_unit': unit_cost})

        # if self.kg_overhead_line:
        #     self.kg_create_move()
        #     return True
        return True

    ## Changes in Button mark done default function (For Normal wastage and Abnormal Wastage) ##
    def button_mark_done(self):
        if not any(rec.jumbo_roll and rec.lot_ids for rec in self.move_raw_ids):
            raise ValidationError(_('You need to supply a Lot/serial number for jumbo roll products'))
        if any(rec.jumbo_roll and rec.lot_ids for rec in self.move_raw_ids):
            self.action_generate_serial()
            res = super(mrp_production, self).button_mark_done()
            for wo in self.workorder_ids:
                if wo.time_ids.filtered(lambda x: (not x.date_end) and (x.loss_type in ('productive', 'performance'))):
                    raise UserError(_('Work order %s is still running') % wo.name)
            normal_wastage = self.env.ref('kg_ultracare_manufacturing.stock_location_normal_wastage_wh')
            abnormal_wastage = self.env.ref('kg_ultracare_manufacturing.stock_location_abnormal_wastage_wh')
            virtual_location = self.env['stock.location'].search([('name', '=', 'Virtual Locations')])
            location_id = self.env['stock.location'].search(
                [('name', '=', 'Production'), ('location_id', '=', virtual_location.id)])
            if self.move_raw_ids:
                for i in self.move_raw_ids:
                    if i.normal_wastage > 0:
                        picking = self.env['stock.move.line'].create({
                            'date': datetime.datetime.now(),
                            'reference': self.name,
                            'product_id': i.product_id.id,
                            'location_id': i.location_dest_id.id,
                            'location_dest_id': normal_wastage.id,
                            'company_id': self.env.user.company_id.id,
                            'qty_done': i.normal_wastage,
                            'product_uom_id': i.product_uom.id,
                            'create_uid': self.env.user.id,
                            'production_id': self.id,
                            'state': 'done',
                            'move_id': i.id,
                            'is_wastage': True
                        })
            if self.abnormal_wastage_id:
                for i in self.abnormal_wastage_id:
                    if i.waste_qty > 0:
                        picking = self.env['stock.move.line'].create({
                            'date': datetime.datetime.now(),
                            'reference': self.name,
                            'product_id': i.product_id.id,
                            'location_id': location_id.id,
                            'location_dest_id': abnormal_wastage.id,
                            'company_id': self.env.user.company_id.id,
                            'qty_done': i.waste_qty,
                            'product_uom_id': i.uom_id.id,
                            'create_uid': self.env.user.id,
                            'production_id': self.id,
                            'state': 'done',
                            'move_id': i.move_id.id,
                            'is_wastage': True
                        })
            return res

    ## For Opening Abnormal Wastage wizard ##
    def open_abnormal_wastage(self):
        ctx = {
            'default_product_id': self.product_id.id,
            'default_user_id': self.user_id.id,
            'default_bill_of_material': self.bom_id.id,
            'default_manufacturing_id': self.id,
            'default_uom_id': self.product_id.uom_id.id,
        }
        action = {
            'name': 'Abnormal Wastage',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'abnormal.wastage',
            'context': ctx,
            'target': 'new'
        }
        return action

    ## Updating Normal Wastage while loading from BOM ##
    def _get_move_raw_values(self, product_id, product_uom_qty, product_uom, operation_id=False, bom_line=False):
        """ Warning, any changes done to this method will need to be repeated for consistency in:
            - Manually added components, i.e. "default_" values in view
            - Moves from a copied MO, i.e. move.create
            - Existing moves during backorder creation """
        source_location = self.location_src_id
        data = {
            'sequence': bom_line.sequence if bom_line else 10,
            'name': _('New'),
            'date': self.date_planned_start,
            'date_deadline': self.date_planned_start,
            'bom_line_id': bom_line.id if bom_line else False,
            'picking_type_id': self.picking_type_id.id,
            'product_id': product_id.id,
            'product_uom_qty': product_uom_qty,
            'product_uom': product_uom.id,
            'location_id': source_location.id,
            'location_dest_id': self.product_id.with_company(self.company_id).property_stock_production.id,
            'raw_material_production_id': self.id,
            'company_id': self.company_id.id,
            'operation_id': operation_id,
            'price_unit': product_id.standard_price,
            'procure_method': 'make_to_stock',
            'origin': self._get_origin(),
            'state': 'draft',
            'warehouse_id': source_location.warehouse_id.id,
            'group_id': self.procurement_group_id.id,
            'propagate_cancel': self.propagate_cancel,
            'normal_wastage': (bom_line.normal_wastage / bom_line.bom_id.product_qty) * self.product_qty,
        }
        return data

    ## For Restricting changing of qty from creating production plan ##
    def write(self, vals):
        res = super(mrp_production, self).write(vals)
        if self.qty_producing and self.product_qty:
            if not self.state == 'draft' and self.qty_producing != self.product_qty:
                raise UserError("You can change quantity in draft stage only")
        return res

    @api.depends('company_id', 'bom_id', 'product_id', 'product_qty', 'product_uom_id', 'location_src_id',
                 'date_planned_start')
    def _compute_move_raw_ids(self):
        for production in self:
            if production.state != 'draft':
                continue

            """ THIS IS THE LINES STORING DEFAULT DATA IN MOVE RAW IDS FOR KEEPING EXISTING DATA AND ADDING NEW LINES"""
            list_move_raw = [Command.link(move.id) for move in
                             production.move_raw_ids.filtered(lambda m: not m.bom_line_id)]
            for i in list_move_raw:
                print(i, "LLLLLLLLLL")
            # list_move_raw = []
            if not production.bom_id and not production._origin.product_id:
                production.move_raw_ids = list_move_raw
            if production.bom_id != production._origin.bom_id:
                production.move_raw_ids = [Command.clear()]
            if production.bom_id and production.product_id and production.product_qty > 0:
                # keep manual entries
                moves_raw_values = production._get_moves_raw_values()
                move_raw_dict = {move.bom_line_id.id: move for move in
                                 production.move_raw_ids.filtered(lambda m: m.bom_line_id)}
                for move_raw_values in moves_raw_values:
                    if move_raw_values['bom_line_id'] in move_raw_dict:
                        # update existing entries
                        list_move_raw += [
                            Command.update(move_raw_dict[move_raw_values['bom_line_id']].id, move_raw_values)]
                    else:
                        # add new entries
                        list_move_raw += [Command.create(move_raw_values)]
                print(list_move_raw, "FINALLLLLL")
                # production.move_raw_ids = False
                production.move_raw_ids = list_move_raw
            else:
                production.move_raw_ids = [Command.delete(move.id) for move in
                                           production.move_raw_ids.filtered(lambda m: m.bom_line_id)]
