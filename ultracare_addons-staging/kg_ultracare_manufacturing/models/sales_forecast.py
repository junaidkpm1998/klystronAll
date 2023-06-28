from datetime import datetime, date

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleForecast(models.Model):
    _name = 'kg.sales.forecast'
    _description = 'Sale Forecast'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = 'id desc'

    def button_approve(self):
        # self.create_pur_req()
        self.create_prod_plan()
        self.kg_state = 'approved'
        # for i in self.kg_lines:
        #     if i.sale_line_id:
        #         i.sale_line_id.kg_sf_line = self.id

    def button_rejected(self):
        self.kg_state = 'rejected'

    def button_set_to_new(self):
        self.kg_state = 'new'

    def button_cancel(self):
        production_plan = self.env['production.planning'].search([('kg_sf_id', '=', self.id)])
        for plan in production_plan:
            if plan.state != 'cancel':
                raise UserError(_('some production planning not in cancelled state'))
        self.kg_state = 'cancel'

    kg_state = fields.Selection([
        ('new', 'New'),
        ('approved', 'Approved'), ('done', 'Done'),
        ('rejected', 'Rejected'),
        ('cancel', 'Cancelled')], string='State',
        copy=False, default='new', track_visibility='onchange')
    name = fields.Char('Name')
    kg_period = fields.Many2one('kg.period', 'Period')
    kg_user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user and self.env.user.id or False)
    kg_date = fields.Date('Requested Date', default=fields.Date.today())
    kg_dep = fields.Many2one('hr.department', 'Department')
    kg_lines = fields.One2many('kg.sf.lines', 'kg_sf_id', 'Lines')
    note = fields.Text('Type Here')
    kg_prod_plan_count = fields.Integer('Plan Count', compute='compute_plan_count')
    # project_id = fields.Many2one('account.analytic.account', 'Cost Center')
    purchase_req_created = fields.Boolean('Purchase Req Created')
    active = fields.Boolean('Active', default=True)
    is_plan = fields.Boolean("Is Plan Created", default=False)
    sale_ids = fields.Many2many('sale.order', 'kg_sale_order_rel', string="Sale Order Id")

    # @api.constrains('kg_state')
    # def check_multiple_open_sf(self):

    def button_group_sf(self):
        period = None
        for record in self:
            if period is not None:
                if record.kg_period.id != period.id:
                    raise UserError(_('Only Same Period Are Allowed'))
                if record.kg_state != 'approved':
                    raise UserError(_('Only Approved Are Allowed'))
            period = record.kg_period
        vals = {}
        vals['kg_period'] = period.id
        vals['kg_dep'] = 2
        vals['purchase_req_created'] = False
        vals['kg_state'] = 'approved'
        sf_id = self.create(vals)
        for record in self:
            record.write({'active': False})

            for line in record.kg_lines:
                check = self.env['kg.sf.lines'].search(
                    [('kg_product_id', '=', line.kg_product_id.id), ('kg_sf_id', '=', sf_id.id)])
                if not check:
                    vals_lines = {}
                    vals_lines['kg_product_id'] = line.kg_product_id.id
                    vals_lines['kg_qty'] = line.kg_qty
                    vals_lines['kg_adj'] = line.kg_adj
                    vals_lines['kg_sf_id'] = sf_id.id
                    vals_lines['kg_uom_id'] = line.kg_uom_id.id
                    self.env['kg.sf.lines'].create(vals_lines)
                else:
                    prev_qty = check.kg_qty
                    prev_adj = check.kg_adj
                    new_qty = prev_qty + (line.kg_qty)
                    new_adj = prev_adj + (line.kg_adj)
                    check.write({'kg_qty': new_qty, 'kg_adj': new_adj})
        return True

    # def compute_plan_count(self):
    #     for record in self:
    #         plan_obj = self.env['kg.prod.plan']
    #
    #         record.kg_prod_plan_count = plan_obj.search_count([('kg_sf_id', '=', record.id)])

    def create_prod_plan(self):
        shift = self.env['shift.master'].search([('name', '=', 'A')])
        # kg_state = self.kg_state
        # if kg_state != 'approved':
        #     raise UserError(_('Approve first'))
        for record in self:
            if not record.kg_lines:
                raise UserError(_('No Products Found'))
            else:
                lines = []
                for line in record.kg_lines:
                    lines.append((0, 0, {
                        'kg_product': line.kg_product_id.id,
                        'kg_date': record.kg_date,
                        'kg_qty': line.kg_qty,
                        'kg_shift_id': shift.id,
                    }))
                plan = self.env['production.planning'].create({
                    'kg_start_date': record.kg_period.date_from,
                    'kg_sf_id': record.id,
                    'kg_shift_lines': lines
                })
                plan.onchange_start_date()
                plan.onchange_kg_end_date()
                plan.kg_shift_lines.onchange_product()
                plan.kg_shift_lines.onchange_date()
        self.write({'is_plan': True})
        return True

    def action_open_production_planning(self):
        return {
            'name': 'Production Planning',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'production.planning',
            'domain': [('kg_sf_id', '=', self.id)],
            'target': 'current'
        }

    # def action_open_purchase_requisition(self):
    #     return {
    #         'name': 'Purchase Requisition',
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'tree,form',
    #         'res_model': 'kg.purchase.req',
    #         'domain': [('kg_sf_id', '=', self.id)],
    #         'target': 'current'
    #     }
    #
    # def create_pur_req(self):
    #     # kg_purchase_requisition_id = record.purchase_req_created and record.kg_purchase_requisition_id.id
    #     if self.purchase_req_created is True:
    #         raise UserError(_('Already purchase requisition created'))
    #     for prod in self.kg_lines:
    #         bom_obj = self.env['mrp.bom'].search([('product_tmpl_id', '=', prod.kg_product_id.product_tmpl_id.id)])
    #         if not bom_obj:
    #             raise UserError(_('Create BOM for product: %s') % prod.kg_product_id.name)
    #         for bom_line in bom_obj.bom_line_ids:
    #             check = self.env['kg.purchase.req'].search(
    #                 [('kg_sf_id', '=', self.id), ('kg_product', '=', bom_line.product_id.id)])
    #             if not check:
    #                 kg_product = bom_line.product_id.id
    #                 kg_product_uom = bom_line.product_uom_id.id
    #                 kg_date = self.kg_date
    #                 # required_date = self.req_date
    #                 # notes = self.notes
    #                 kg_qty = (prod.kg_net) * (bom_line.product_qty)
    #                 # kg_prod_plan_id = self.kg_prod_plan_id and self.kg_prod_plan_id.id
    #                 state = 'new'
    #                 vals = {'kg_product': kg_product,
    #                         'kg_product_uom': kg_product_uom,
    #                         'kg_date': kg_date,
    #                         'kg_qty': kg_qty,
    #                         'kg_sf_id': self.id,
    #                         'state': state}
    #                 self.env['kg.purchase.req'].create(vals)
    #             else:
    #                 old_qty = check.kg_qty
    #                 val = (bom_line.product_qty) * (prod.kg_net)
    #                 new = old_qty + val
    #                 check.write({'kg_qty': new})
    #             self.write({'purchase_req_created': True})

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'sales_forecast.sequence') or 'New'
        sales_sf = self.env['kg.sales.forecast'].search([('kg_state', '=', 'new')])
        if sales_sf:
            raise UserError(_("Record already exist in draft stage"))
        result = super(SaleForecast, self).create(vals)
        return result


class SaleForecastline(models.Model):
    _name = 'kg.sf.lines'
    _description = 'Sale Forcast Line'

    @api.depends('kg_adj', 'kg_qty')
    def _compute_net(self):
        for record in self:
            record.kg_net = record.kg_qty + record.kg_adj

    name = fields.Char('Name')
    priority_no = fields.Integer("Priority")
    kg_product_id = fields.Many2one('product.product', 'Product')
    kg_uom_id = fields.Many2one("uom.uom", related='kg_product_id.uom_id', string="UOM", readonly=True)
    kg_qty = fields.Float('Qty')
    kg_adj = fields.Float('Adjustments')
    kg_net = fields.Float('Net', compute='_compute_net', store=True)
    kg_comments = fields.Char('Comments')
    kg_sf_id = fields.Many2one('kg.sales.forecast', 'Sales Forecast', ondelete='cascade')
    state = fields.Selection(related='kg_sf_id.kg_state')
    sale_id = fields.Many2one('sale.order', string="Sale ID")
    sale_line_id = fields.Many2one('sale.order.line', string="Sale Line ID")
    expected_date = fields.Datetime(related='sale_line_id.expected_delivery', string="Expected Delivery")


class SalesForecastOld(models.Model):
    _name = 'kg.sale.forecast'

    name = fields.Char("Name")
