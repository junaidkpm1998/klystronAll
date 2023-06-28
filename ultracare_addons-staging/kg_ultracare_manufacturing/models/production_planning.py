from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from datetime import datetime

from odoo.exceptions import UserError, ValidationError


class ProductionPlanning(models.Model):
    _name = 'production.planning'
    _description = 'Production Planning'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = 'name desc'

    def make_it_done(self):
        for i in self.kg_dummy_ids:
            i.shift_id.write({'raw_material_ids': [(4, i.id)]})
        mail_template = self.env.ref('kg_ultracare_manufacturing.production_planning_confirmation_email')
        mail_template.send_mail(self.id, force_send=True)
        self.state = 'done'

    def make_it_progress(self):
        self.state = 'progress'

    state = fields.Selection([
        ('new', 'New'),
        ('progress', 'In Progress'),
        ('done', 'Done'),
        ('return', 'Returned')], string='State',
        copy=False, default='new', track_visibility='onchange')
    name = fields.Char('Name', default='New')
    kg_start_date = fields.Date('Start Date')
    kg_start_day = fields.Char('Start Day')
    kg_end_date = fields.Date('End Date')
    kg_end_day = fields.Char('End Day')
    kg_shift_lines = fields.One2many('product.shift.line', 'kg_prod_plan_id', 'Shift Lines')
    kg_prod_line = fields.One2many('product.shift.line', 'kg_prod_plan_id', 'Product Lines',
                                   compute='compute_prod_line')
    kg_dummy_ids = fields.One2many('production.dummy.line', 'prod_id', 'Dummy Lines')
    kg_dummy_product_ids = fields.One2many('production.dummy.products', 'prod_id', 'Dummy Products')
    show_raw = fields.Boolean('SHOW RAW', copy=False)
    is_mo_created = fields.Boolean(string="Is MO Created",
                                   help="Checking whether Manufacturing order is created or not")
    pending_mo = fields.Boolean(string='Pending MO', compute='compute_pending_qty', default=False, store=True)

    mo_check = fields.Boolean(string="Is MO Check", default=False)
    mo_balance_check = fields.Float(string="MO Balance", compute='compute_mo_balance')

    @api.depends('kg_shift_lines')
    def compute_mo_balance(self):
        if self.kg_shift_lines:
            amt = sum(self.kg_shift_lines.mapped('kg_balance'))
            if amt > 0.00:
                self.mo_balance_check = amt
            else:
                self.mo_balance_check = 0.00
        else:
            self.mo_balance_check = 0.00

    # @api.depends('kg_shift_lines')
    # def _compute_ready_mo(self):
    #     shift = []
    #     for rec in self:
    #         if rec.kg_shift_lines:
    #             length_shift = len(rec.kg_shift_lines)
    #             for line in rec.kg_shift_lines:
    #                 if line.ready_mo:
    #                     shift.append(line.ready_mo)
    #             len_ready_mo = len(shift)
    #             if length_shift == len_ready_mo:
    #                 rec.mo_check = True
    #             else:
    #                 rec.mo_check = False

    def compute_pending_qty(self):
        for pp in self:
            for line in self.kg_shift_lines:
                if line.kg_balance > 0:
                    pp.pending_mo = True
                    break
                else:
                    pp.pending_mo = False

    def compute_prod_line(self):
        ### get recordset of related object, for example with search (or whatever you like):
        related_recordset = self.env["product.shift.line"].search([("kg_prod_plan_id", "=", self.id)])
        test_list = {}
        for i in related_recordset:
            test_list[i.id] = i.kg_product.id
        inv = dict()
        for (k, v) in test_list.items():
            inv[v] = k
        ids = []
        for j in inv:
            ids.append(inv[j])
        records = self.env["product.shift.line"].browse(ids)
        self.kg_prod_line = records

    kg_raw_mat_lines = fields.One2many('kg.raw.mat.line', 'kg_prod_plan_id', 'Raw Material Lines')
    kg_sf_id = fields.Many2one('kg.sales.forecast', 'Sales Forecast')

    project_id = fields.Many2one('account.analytic.account', 'Cost Center')
    product_transfer_id = fields.Many2one('kg.product.transfer', 'Product Transfer')

    @api.onchange('kg_end_date')
    def onchange_kg_end_date(self):
        if self.kg_end_date:
            self.kg_end_day = self.kg_end_date.strftime("%A")

    ## Return of Raw material ##
    def return_raw_mat(self):
        for record in self:
            plan_obj = self
            vals_picking = {}
            # <<<<<<<<<<<<<<<Search for picking type and location>>>>>>>>>>>>>>>>
            vals_picking['picking_type_id'] = self.env['stock.picking.type'].search(
                [('code', '=', 'internal')], limit=1).id
            vals_picking['location_id'] = self.env['stock.location'].search(
                [('name', '=', 'Production'), ('usage', '=', 'internal')], limit=1).id
            vals_picking['location_dest_id'] = 15
            vals_picking['kg_prod_plan_id'] = plan_obj.id
            pick_id = self.env['stock.picking'].create(vals_picking)
            for line in plan_obj.kg_shift_lines:
                qty = line.kg_balance
                if qty != 0:
                    bom_obj = self.env['mrp.bom'].search([('product_tmpl_id', '=', line.kg_product.product_tmpl_id.id)])
                    if not bom_obj:
                        raise UserError(_('Create BOM for product: %s') % line.kg_product.name)
                    for bom_line in bom_obj.bom_line_ids:
                        dummy = False
                        product_id = bom_line.product_id
                        check = self.env['stock.move'].search(
                            [('picking_id', '=', pick_id.id), ('product_id', '=', product_id.id)])
                        if not check:
                            vals = {}
                            vals['product_id'] = product_id.id
                            vals['name'] = product_id.name
                            vals['product_uom_qty'] = (bom_line.product_qty) * qty
                            # vals['kg_req_date'] = line.kg_date
                            vals['product_uom'] = bom_line.product_uom_id.id
                            vals['location_id'] = self.env['stock.location'].search(
                                [('name', '=', 'Production'), ('usage', '=', 'internal')], limit=1).id
                            vals['location_dest_id'] = self.env['stock.location'].search(
                                [('name', '=', 'Stock'), ('usage', '=', 'internal')], limit=1).id
                            vals['picking_id'] = pick_id.id
                            self.env['stock.move'].create(vals)
                        else:
                            prev_qty = check.product_uom_qty
                            val = (bom_line.product_qty) * qty
                            new_qty = prev_qty + val
                            check.write({'product_uom_qty': new_qty})
            self.state = 'return'
            return True

    @api.onchange('kg_sf_id')
    def onchange_sale_forcast(self):
        prod_shft_line_objs = self.env['product.shift.line']
        for record in self:
            if self.kg_sf_id:
                for line in self.kg_sf_id.kg_lines:
                    data = {
                        'kg_product': line.kg_product_id and line.kg_product_id.id,
                        'kg_qty': line.kg_net,
                    }
                    line = prod_shft_line_objs.new(data)
                    prod_shft_line_objs += line
            record.kg_shift_lines = prod_shft_line_objs

    @api.onchange('kg_start_date')
    def onchange_start_date(self):
        for record in self:
            if record.kg_sf_id:
                record.kg_end_date = record.kg_sf_id.kg_period.date_to
                record.kg_start_day = record.kg_sf_id.kg_period.date_from.strftime("%A")
            else:
                if record.kg_start_date:
                    start_dt = fields.Datetime.from_string(record.kg_start_date)
                    dt = start_dt + relativedelta(days=4)
                    record.kg_end_date = fields.Datetime.to_string(dt)
                    record.kg_start_day = record.kg_start_date.strftime("%A")

    @api.onchange('kg_product')
    def onchange_product(self):
        for record in self:
            record.kg_pack = record.kg_product.kg_pack and record.kg_product.kg_pack.id or False
            record.kg_core = record.kg_product.kg_core and record.kg_product.kg_core.id or False
            record.kg_lbl = record.kg_product.kg_lbl
            record.kg_hndl = record.kg_product.kg_hndl
            record.kg_emb = record.kg_product.kg_emb
            record.kg_lam = record.kg_product.kg_lam
            record.kg_width = record.kg_product.kg_width
            record.kg_perf = record.kg_product.kg_perf
            record.kg_dia = record.kg_product.kg_dia
            record.kg_sht = record.kg_product.kg_sht
            record.kg_ply = record.kg_product.kg_ply
            record.kg_gsm = record.kg_product.kg_gsm
            record.kg_wght = record.kg_product.kg_wght
            record.kg_trrt = record.kg_product.kg_trrt
            record.kg_cph = record.kg_product.kg_cph

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('production.planning.sequence') or _('New')
        return super(ProductionPlanning, self).create(vals)

    def get_actual_prod(self, dummy):
        for plan in self:
            line = self.env['production.dummy.products'].search([('prod_id', '=', plan.id),
                                                                 ('kg_product_id', '=', dummy.id)], limit=1)
            if line:
                return line.actual_product_id
            else:
                raise ValidationError('No Actual product defined for %s' % dummy.name)

    ## Material Requisition for PP ##
    def generate_mat(self):
        plan_obj = self
        vals_picking = {}
        vals_picking['picking_type_id'] = self.env['stock.picking.type'].search(
            [('code', '=', 'internal')], limit=1).id
        vals_picking['location_id'] = self.env['stock.location'].search(
            [('name', '=', 'Stock'), ('usage', '=', 'internal')], limit=1).id
        vals_picking['location_dest_id'] = self.env['stock.location'].search(
            [('name', '=', 'Production'), ('usage', '=', 'internal')], limit=1).id
        pick_id = self.env['stock.picking'].create(vals_picking)
        pick_id.kg_prod_plan_id = self.id
        quant = 0
        for line in plan_obj.kg_shift_lines:
            qty = line.kg_qty
            bom_obj = self.env['mrp.bom'].search([('product_tmpl_id', '=', line.kg_product.product_tmpl_id.id)])
            if not bom_obj:
                raise UserError(_('Create BOM for product: %s') % line.kg_product.name)
            if not plan_obj.kg_dummy_ids:
                raise UserError(_('Kindly Click on the Show Raw Material To continue'))

        for bom_line in plan_obj.kg_dummy_ids:
            if bom_line.production_qty < bom_line.req_qty:
                check = self.env['stock.move'].search(
                    [('picking_id', '=', pick_id.id), ('product_id', '=', bom_line.kg_product_id.id)])
                if not check:
                    quant += (bom_line.req_qty)
                    vals = {}
                    vals['product_id'] = bom_line.kg_product_id.id
                    vals['name'] = bom_line.kg_product_id.name
                    vals['product_uom_qty'] = (bom_line.req_qty)
                    vals['product_uom'] = bom_line.product_uom_id.id
                    vals['picking_id'] = pick_id.id
                    vals['location_id'] = self.env['stock.location'].search(
                        [('name', '=', 'Stock'), ('usage', '=', 'internal')], limit=1).id
                    vals['location_dest_id'] = self.env['stock.location'].search(
                        [('name', '=', 'Production'), ('usage', '=', 'internal')], limit=1).id
                    move = self.env['stock.move'].create(vals)
                else:
                    prev_qty = check.product_uom_qty
                    val = bom_line.req_qty
                    new_qty = prev_qty + val
                    check.write({'product_uom_qty': new_qty})
        self.state = 'progress'
        pick_id.action_confirm()
        plan_obj.action_open_material_requisition()

    def action_open_material_requisition(self):
        return {
            'name': 'Material Requisition',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('kg_prod_plan_id', '=', self.id)],
            'target': 'current'
        }

    ## Load Raw Material Function ##
    def show_raw_materials(self):
        uid = self.env.uid or 0
        self.env.cr.execute("delete from wizard_production_planning where user_id= %d" % (uid))
        self.kg_dummy_ids = False
        if not self.kg_shift_lines:
            raise UserError(_("Please Add a line in Shift for fetching raw materials"))
        for line in self.kg_shift_lines:
            qty = line.kg_qty
            bom_obj = self.env['mrp.bom'].search([('product_tmpl_id', '=', line.kg_product.product_tmpl_id.id)],
                                                 limit=1)

            if not bom_obj:
                raise UserError(_('Create BOM for product: %s') % line.kg_product.name)
            for bom_line in bom_obj.bom_line_ids:
                purchase_req_qty = (bom_line.product_qty / bom_obj.product_qty) * qty
                prod = []
                location = self.env.ref('stock.stock_location_stock')
                current_stock = self.env['stock.quant'].search([('product_id', '=', bom_line.product_id.id), (
                    'location_id', 'in', location.ids)], limit=1)
                qty_available = current_stock.quantity
                if purchase_req_qty < qty_available:
                    order_qty = 0.00
                else:
                    order_qty = purchase_req_qty - qty_available
                prod.append((0, 0, {
                    'kg_product_id': bom_line.product_id.id,
                    'req_qty': purchase_req_qty,
                    'available_qty': current_stock.quantity,
                    'product_uom_id': bom_line.product_uom_id.id,
                    'prod_id': self.id,
                    'shift_id': line.id,
                    'purchase_req_qty': order_qty,
                }))
                self.write({'kg_dummy_ids': prod,
                            'show_raw': True})

    purchase_req_created = fields.Boolean('Purchase Req Created', copy=False)
    kg_date = fields.Date('Date', default=fields.Date.today())

    ## Purchase Requisition Creation##
    def create_pur_req(self):
        if self.purchase_req_created is True:
            raise UserError(_('Already purchase requisition created'))
        for prod in self.kg_shift_lines:
            bom_obj = self.env['mrp.bom'].search([('product_tmpl_id', '=', prod.kg_product.product_tmpl_id.id)])
            if not bom_obj:
                raise UserError(_('Create BOM for product: %s') % prod.kg_product.name)
        for bom_line in self.kg_dummy_ids:
            if bom_line.purchase_req_qty > 0:
                check = self.env['kg.purchase.req'].search(
                    [('production_planning', '=', self.id), ('kg_product', '=', bom_line.kg_product_id.id)])
                if not check:
                    kg_product = bom_line.kg_product_id.id
                    kg_product_uom = bom_line.product_uom_id.id
                    kg_date = self.kg_date
                    kg_qty = bom_line.purchase_req_qty
                    state = 'new'
                    vals = {'kg_product': kg_product,
                            'kg_product_uom': kg_product_uom,
                            'kg_date': kg_date,
                            'kg_qty': kg_qty,
                            'kg_sf_id': self.kg_sf_id.id,
                            'state': state,
                            'production_planning': self.id,
                            'purchasing_qty': bom_line.purchase_req_qty
                            }
                    purchase = self.env['kg.purchase.req'].create(vals)
                    purchase.onchange_purchase_qty()
                else:
                    old_qty = check.kg_qty
                    val = bom_line.req_qty
                    new = old_qty + val
                    check.write({'kg_qty': new, 'purchasing_qty': new})
                self.write({'purchase_req_created': True})

    def action_open_purchase_requisition(self):
        return {
            'name': 'Purchase Requisition',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'kg.purchase.req',
            'domain': [('production_planning', '=', self.id)],
            'target': 'current'
        }

    ## Change Dummy Product Wizard ##
    def action_show_dummy_products(self):
        prod = []
        for i in self.kg_dummy_ids:
            if i.kg_product_id.is_dummy_prod:
                prod.append((0, 0, {
                    'dummy_product_id': i.kg_product_id.id,
                    'shift_line_id': i.shift_id.id,
                    'dummy_line_id': i.id,
                    'production_plan_id': i.prod_id.id,
                }))
        ctx = {
            'default_production_plan_id': self.id,
            'default_dummy_line_ids': prod
        }
        action = {
            'name': 'Create',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.wise.dummy',
            'context': ctx,
            'target': 'new'
        }
        return action

    ## For creating Manufacturing Order From PP ##
    def action_create_mo(self):
        shift = []
        for rec in self:
            if rec.kg_shift_lines:
                length_shift = len(rec.kg_shift_lines)
                for line in rec.kg_shift_lines:
                    if line.kg_balance > 0:
                        if line.kg_act_prod > line.kg_balance:
                            raise UserError(
                                "You cannot create manufacturing order morethan balance amount."
                                "\n Please change TO DO in lines ")
                    if line.ready_mo:
                        shift.append(line.ready_mo)
                len_ready_mo = len(shift)
                if length_shift == len_ready_mo:
                    rec.mo_check = True
                else:
                    rec.mo_check = False
            # rec._set_qty_producing()
        for i in self.kg_shift_lines:
            i.complete_prod()
        self.is_mo_created = True

        return {
            'name': 'Manufacturing Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'mrp.production',
            'domain': [('production_planning_id', '=', self.id)],
            'target': 'current'
        }

    def action_open_manufacturing_order(self):
        return {
            'name': 'Manufacturing Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'mrp.production',
            'domain': [('production_planning_id', '=', self.id)],
            'target': 'current'
        }


class ProductionPlanningWizard(models.TransientModel):
    _name = 'wizard.production.planning'
    _description = 'Production Planning'

    kg_product_id = fields.Many2one("product.product", string="Product")
    req_qty = fields.Float(string="Required Quantity")
    available_qty = fields.Float(string="Available Quantity", compute='_compute_prod_qty')
    user_id = fields.Many2one('res.users', 'Requested By', default=lambda self: self.env.user)
    shift_id = fields.Many2one('product.shift.line', 'Shift Id')

    def _compute_prod_qty(self):
        locations = self.env['stock.location'].search([('name', '=', 'Stock'), ('usage', '=', 'internal')])
        for obj in self:
            qty = 0
            for li in locations:
                qty += obj.kg_product_id.with_context({'location': li.id}).qty_available
            obj.available_qty = qty


class ProductionPlanningDummyLine(models.Model):
    _name = 'production.dummy.line'
    _description = 'Production Dummy Line'

    kg_product_id = fields.Many2one("product.product", string="Product")
    req_qty = fields.Float(string="Required Quantity")
    available_qty = fields.Float(string="Available Quantity", compute='_compute_prod_qty')
    user_id = fields.Many2one('res.users', 'Requested By', default=lambda self: self.env.user)
    prod_id = fields.Many2one('production.planning', "Production ID", readonly=True)
    is_dummy = fields.Boolean("Is Dummy", default=False, compute='_compute_dummy_product',
                              help="Checking weather the product is dummy or not")
    product_uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure')
    product_uom_qty = fields.Float(string='Total Quantity')
    production_qty = fields.Float('Production Stock', compute='_compute_production_qty')
    dummy_line = fields.Boolean(string="Dummy Line")
    shift_id = fields.Many2one('product.shift.line', 'Shift Id')
    purchase_req_qty = fields.Float("To Order Quantity", compute='_onchange_product_del')
    is_in_stock = fields.Boolean(string="Is In Available Stock", compute='compute_stock')

    @api.depends('available_qty')
    @api.onchange('available_qty')
    def compute_stock(self):
        for i in self:
            print(i.available_qty, "______", i.req_qty)
            if i.available_qty >= i.req_qty:
                i.is_in_stock = True
                i.write({'purchase_req_qty': 0.00})
            else:
                i.is_in_stock = False

    @api.onchange('kg_product_id', 'req_qty', 'available_qty', 'production_qty')
    @api.depends('req_qty', 'production_qty')
    def _onchange_product_del(self):
        for rec in self:
            if rec.kg_product_id:
                rec.product_uom_id = rec.kg_product_id.uom_id
                rec.available_qty = rec.kg_product_id.qty_available
                if rec.req_qty <= rec.production_qty:
                    rec.purchase_req_qty = 0.00
                else:
                    rec.purchase_req_qty = rec.req_qty - rec.production_qty

    @api.depends('kg_product_id')
    def _compute_dummy_product(self):
        for i in self:
            if i.kg_product_id:
                if i.kg_product_id.is_dummy_prod:
                    i.is_dummy = True
                else:
                    i.is_dummy = False
            else:
                i.is_dummy = False

    def _compute_prod_qty(self):
        locations = self.env['stock.location'].search([('name', '=', 'Stock'), ('usage', '=', 'internal')])
        for obj in self:
            qty = 0
            for li in locations:
                qty += obj.kg_product_id.with_context({'location': li.id}).qty_available
            obj.available_qty = qty

    def _compute_production_qty(self):
        locations = self.env['stock.location'].search([('name', '=', 'Production'), ('usage', '=', 'internal')])
        for obj in self:
            qty = 0
            for li in locations:
                qty += obj.kg_product_id.with_context({'location': li.id}).qty_available
            obj.production_qty = qty


class ProductionDummyProducts(models.Model):
    _name = 'production.dummy.products'
    _description = 'Production Dummy products'

    kg_product_id = fields.Many2one("product.product", string="Product")
    req_qty = fields.Float(string="Required Quantity")
    available_qty = fields.Float(string="Available Quantity", compute='_compute_prod_qty')
    user_id = fields.Many2one('res.users', 'Requested By', default=lambda self: self.env.user)
    prod_id = fields.Many2one('production.planning', "Production ID", readonly=True)
    is_dummy = fields.Boolean("Is Dummy", default=False, compute='_compute_dummy_product',
                              help="Checking weather the product is dummy or not")
    product_uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure')
    product_uom_qty = fields.Float(string='Total Quantity')
    production_qty = fields.Float('Production Stock', compute='_compute_production_qty')

    dummy_line = fields.Boolean(string="Dummy Line")
    actual_product_id = fields.Many2one('product.product', "Actual Product")

    def _compute_production_qty(self):
        locations = self.env['stock.location'].search([('name', '=', 'Production'), ('usage', '=', 'internal')])
        for obj in self:
            qty = 0
            for li in locations:
                qty += obj.kg_product_id.with_context({'location': li.id}).qty_available
            obj.production_qty = qty

    @api.depends('kg_product_id')
    def _compute_dummy_product(self):
        for i in self:
            if i.kg_product_id:
                if i.kg_product_id.is_dummy_prod:
                    i.is_dummy = True
                else:
                    i.is_dummy = False
            else:
                i.is_dummy = False

    def _compute_prod_qty(self):
        locations = self.env['stock.location'].search([('name', '=', 'Stock'), ('usage', '=', 'internal')])
        for obj in self:
            qty = 0
            for li in locations:
                qty += obj.kg_product_id.with_context({'location': li.id}).qty_available
            obj.available_qty = qty
