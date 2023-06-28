import dateutil.utils

from odoo import models, fields, api
import datetime


class ProductWarranty(models.Model):
    _name = "warranty.model"
    _rec_name = "name"

    invoice_id = fields.Many2one('account.move',
                                 domain="[('state', '!=', 'draft') , ('move_type', '=', 'out_invoice')]" ,required=True)
    product_id = fields.Many2one('product.product')
    lot_id = fields.Many2one('stock.lot')
    request_date = fields.Date(readonly=True, default=dateutil.utils.today())
    customer_name = fields.Many2one(related='invoice_id.partner_id')

    purchase_date = fields.Date(related='invoice_id.invoice_date', string="Purchase Date")
    # seq_number = fields.Text()
    name = fields.Char(string='Sequence Number', readonly=True, default=lambda self: "New")
    company_id = fields.Many2one('res.company', store=True, copy=False,
                                 string="Company",
                                 default=lambda self: self.env.company)
    warranty_periods = fields.Integer(related="product_id.warranty_periods")
    val_new = fields.Date(compute='compute_date', string="Warranty Expiry Date")
    warranty_type_flag = fields.Boolean(default=False)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'Submit'),
        ('approved', 'Approved'),
        ('received', 'Received'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], default='draft')

    def to_approve(self):
        self.write({
            'state': 'to_approve',
        })

    def approved(self):
        self.write({
            'state': 'approved',
        })
        if self.product_id.warranty_type:
            self.write({
                'state': 'received',
            })
            self.warranty_type_flag = True
            move = self.env['stock.move'].create({
                'name': 'Warranty Product',
                'location_id': self.env.ref('stock.stock_location_customers').id,
                'location_dest_id': self.env.ref('product_warranty.warranty_location').id,
                'product_id': self.product_id.id,
                'product_uom_qty': '1',
                'origin': self.name

            })
            move._action_confirm()
            move.move_line_ids.write(
                {'qty_done': '1'})
            move._action_done()

    def product_return(self):
        self.write({
            'state': 'done',
        })
        move = self.env['stock.move'].create({
            'name': 'Warranty Product',
            'location_id': self.env.ref('product_warranty.warranty_location').id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'product_id': self.product_id.id,
            'origin': self.name,
            'product_uom_qty': '1',

        })
        move._action_confirm()
        move.move_line_ids.write(
            {'qty_done': '1'})
        move._action_done()

    def cancel(self):
        self.write({
            'state': 'cancel',
        })

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'warranty.model') or 'New'
        res = super(ProductWarranty, self).create(vals)
        return res

    @api.onchange('invoice_id')
    def onchange_invoice(self):
        val = self.invoice_id.invoice_line_ids.product_id
        return {'domain': {'product_id': [('id', '=', val.ids)]}}

    @api.onchange('product_id')
    def onchange_product(self):
        val = self.product_id
        v = {'domain': {'lot_id': [('product_id', 'in', val.ids)]}}
        print(v, '@!!!!!!!!!!!!!!!!!!!!!!')
        print(self.lot_id)
        return v

    @api.depends('purchase_date')
    def compute_date(self):
        if self.purchase_date:
            self.val_new = self.purchase_date + datetime.timedelta(days=self.product_id.warranty_periods)
        return self.val_new

    def product_move(self):
        # res = self.search([])
        # self = self | res
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock move',
            'view_mode': 'tree',
            'view_id': self.env.ref('stock.view_move_tree').id,
            'res_model': 'stock.move',
            'domain': [('origin', '=', self.name)],
            # 'context': "{}"
        }

    def get_product(self, inv_id):
        prdct_val = self.env['account.move'].browse(int(inv_id))
        products = prdct_val.invoice_line_ids.product_id
        print(prdct_val, products)
        dict = []
        for i in products:
            dict.append({
                i.id: i.name
            })
        print(dict)
        return dict

    def get_lot(self, prod_id):
        print("hhhuuuuu")

        # prd_val = self.env['product.template'].browse(int(prod_id))
        # val = self.product_id
        prd_val = self.env['product.product'].browse(int(prod_id))
        lot = prd_val.stock_connection.name
        # print((lot),"looooooozzzzzzzzzzz")

        # lot_val = {'domain': {'lot_id': [('prod_id', 'in', val.ids)]}}
        # lot_valqq = prod_id.optional_product_ids
        # return {'domain': {'lot_id': [('product_id', 'in', val.ids)]}}

        # print(lot_valqq, "lottt val")
        print(prod_id)
        print(self, "self")
        # print(lot_id, "lot_id")
        # print(val, "val")
        dict1 = []
        # for i in lot:
        # print(type(i))
        dict1.append({
            lot: lot
        })

        print(dict1, "dict1")
        return dict1
