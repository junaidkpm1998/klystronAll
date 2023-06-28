# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo import tools
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError, AccessError
from odoo import api, fields, models, SUPERUSER_ID, _


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    ack_prod = fields.Boolean('Ack By Production', default=False, readonly=True)

    # warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')

    def ack_by_prod(self):
        for record in self:
            record.write({'ack_prod': True})


class kg_mat_req(models.Model):
    _name = 'kg.mat.req'
    _description = 'Material Request'

    def create_picking_id(self):
        for record in self:
            vals = {}
            vals['picking_type_id'] = self.env['stock.picking.type'].search(
                [('name', '=', 'Internal Transfers to production location')], limit=1).id
            # vals['location_id']=self.env['stock.location'].search([('name','=','Stock'),('usage','=','internal')],limit=1).id
            vals['location_id'] = 15
            vals['location_dest_id'] = self.env['stock.location'].search(
                [('name', '=', 'Production'), ('usage', '=', 'internal')], limit=1).id
            pick_id = self.env['stock.picking'].create(vals)
            for line in record.kg_mat_req_lines:
                vals_line = {}
                if line.kg_product:
                    vals_line['product_id'] = line.kg_product.id
                    vals_line['name'] = line.kg_product.name
                vals_line['product_uom_qty'] = line.kg_qty
                # vals_line['location_id']=self.env['stock.location'].search([('name','=','Stock'),('usage','=','internal')],limit=1).id
                vals_line['location_id'] = 15
                vals_line['location_dest_id'] = self.env['stock.location'].search(
                    [('name', '=', 'Production'), ('usage', '=', 'internal')], limit=1).id
                if line.kg_uom:
                    vals_line['product_uom'] = line.kg_uom.id
                vals_line['picking_id'] = pick_id.id
                self.env['stock.move'].create(vals_line)

            record.write({'picking_id': pick_id.id})
            return True

    def open_rfq(self):
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        return action

    def release(self):
        picking_id = self.picking_id and self.picking_id.id
        picking_obj = self.picking_id
        state = picking_obj.state
        if not picking_id:
            raise UserError(_('create and attach transfer document'))
        if state != 'done':
            raise UserError(_('transfer not completed'))
        kg_mrp_id = self.kg_mrp_id and self.kg_mrp_id.id
        if not kg_mrp_id:
            raise UserError(_('Job not defined'))
        mrp_obj = self.kg_mrp_id
        consumed_lines = mrp_obj.move_raw_ids
        for line in consumed_lines:
            line.action_assign()
            if line.state != 'assigned':
                raise UserError(_('recheck the stock for product: %s') % line.product_id.name)
        self.kg_state = 'release'

    def production_ack(self):
        state = self.kg_state
        if state != 'release':
            raise UserError(_('Let store release first'))
        kg_mrp_id = self.kg_mrp_id and self.kg_mrp_id.id
        if not kg_mrp_id:
            raise UserError(_('Job not defined'))
        mrp_obj = self.kg_mrp_id
        consumed_lines = mrp_obj.move_raw_ids
        for line in consumed_lines:
            if line.state != 'assigned':
                line.action_assign()
                if line.state != 'assigned':
                    raise UserError(_('recheck the stock for product: %s') % line.product_id.name)
        self.kg_state = 'ack'
        self.kg_production_ack_by = self.env.user and self.env.user.id

    def done(self):
        self.state = 'done'

    name = fields.Char('Name')
    kg_mrp_id = fields.Many2one('mrp.production', 'Job')

    kg_client = fields.Many2one('res.partner', 'Client')
    kg_project = fields.Many2one('project.project', 'Project')
    # kg_mrp_id = fields.Many2one('mrp.production', 'Job')
    picking_id = fields.Many2one('stock.picking', 'Picking')
    kg_raised_by = fields.Many2one('res.users', 'Raised By',
                                   default=lambda self: self.env.user and self.env.user.id or False)
    kg_assign_to = fields.Many2one('res.users', 'Assigned To')
    kg_production_ack_by = fields.Many2one('res.users', 'Production(Ack)')
    kg_desc = fields.Text('Description')
    kg_availability_date = fields.Date('Availability Date')
    kg_mat_req_lines = fields.One2many('kg.mat.req.lines', 'kg_mat_req_id', 'Lines')
    kg_state = fields.Selection(
        [('draft', 'Draft'), ('release', 'Released'), ('ack', 'Acknowledged By Production'), ('done', 'Done')],
        'Status', default='draft')


class kg_mat_req_lines(models.Model):
    _name = "kg.mat.req.lines"
    _description = 'Material Request Line'

    name = fields.Char('Name')
    kg_product = fields.Many2one('product.product', 'Item')
    kg_req_date = fields.Date('Required Date')
    kg_uom = fields.Many2one('uom.uom', 'UOM')
    kg_qty = fields.Float('Product Qty')
    kg_mat_req_id = fields.Many2one('kg.mat.req', 'Mat Req id')

    @api.onchange('kg_product')
    def onchange_product(self):
        for record in self:
            record.kg_uom = record.kg_product.uom_id.id or False


class kg_mrp_account_lines(models.Model):
    _name = 'kg.mrp.account.lines'
    _description = 'kg.mrp.account.lines'

    kg_mrp_id = fields.Many2one('mrp.production','Production Order')
    product_id = fields.Many2one('product.product','Product')
    account_move_id = fields.Many2one('account.move',string="Number")
    internal_sequence_number = fields.Char(string="Internal Number")
    ref = fields.Char(string="Reference")
    journal_id = fields.Many2one('account.journal',string="Journal")
    amount = fields.Float(string='Amount')
    status = fields.Char(string='Status')


class kg_prod_cost(models.Model):
    _name = "kg.prod.cost"
    _description = 'Product Cost'

    @api.depends('kg_qty_hour', 'kg_cost')
    def _compute_amount(self):
        self.amount = self.kg_qty_hour * self.kg_cost

    kg_product = fields.Many2one('product.product', 'Product')
    kg_qty_hour = fields.Float('Qty/Hour')
    kg_auto = fields.Float('Auto')
    kg_cost = fields.Float('Cost')
    amount = fields.Float(string="Amount", compute="_compute_amount")
    kg_mrp_id = fields.Many2one('mrp.production', 'Production Order')