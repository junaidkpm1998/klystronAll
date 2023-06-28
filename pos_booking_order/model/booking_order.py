from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BookingOrder(models.Model):
    _name = 'booking.order'
    _rec_name = 'reference_no'

    def _default_session(self):
        return self.env['pos.session'].search([('state', '=', 'opened'),
                                               ('user_id', '=', self.env.uid)], limit=1)

    def _default_pricelist(self):
        return self._default_session().config_id.pricelist_id

    reference_no = fields.Char(string='Order Reference', required=True,
                               readonly=True, default=lambda self: _('New'))
    # name = fields.Char(string='Booking Ref', required=True, readonly=True, copy=False, default='/')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id)
    date_quotation = fields.Datetime(string='Quotation Date',
                                     readonly=True, index=True, default=fields.Datetime.now)
    date_order = fields.Date(string='Order Date',
                             readonly=True, index=True, default=fields.Datetime.now)
    amount_tax = fields.Float(compute='_compute_amount_all', string='Taxes', digits=0, default=1.2)
    amount_total = fields.Float(compute='_compute_amount_all', string='Total', digits=0)
    lines = fields.One2many('book.order.line', 'order_id', string='Order Lines', copy=True)
    partner_id = fields.Many2one('res.partner', string='Customer', change_default=True, index=True)
    state = fields.Selection([('draft', 'New'), ('done', 'Done')],
                             'Status', readonly=True, copy=False, default='draft')
    note = fields.Text(string='Internal Notes')
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position')
    book_order_ref = fields.Char(string='Booked Order Ref', readonly=True, copy=False)
    pickup_date = fields.Datetime(string='Pickup Date', readonly=True)
    deliver_date = fields.Datetime(string='Deliver Date', readonly=True)
    phone = fields.Char('Contact no', help='Phone of customer for delivery')
    delivery_address = fields.Char('Delivery Address', help='Address of customer for delivery')
    book_order = fields.Boolean('Booking Order', readonly=True)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist',
                                   default=_default_pricelist)
    total = fields.Integer(compute='_compute_line_total', store=True)
    info = fields.Text(string='Notes')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='Status', default='draft')

    @api.depends('lines.price_subtotal_incl')
    def _compute_line_total(self):
        self.total = sum(self.lines.mapped('price_subtotal_incl'))
        # print("jjjjjjj")

        # for rec in self:
        #     rec.total = sum(rec.lines.mapped('price_subtotal_incl'))
        #     print("Ggggggggg")

        # print("compute")
        # print(sum(self.lines.mapped('price_subtotal_incl')))

    @api.model
    def create(self, vals):
        if vals.get('reference_no', _('New')) == _('New'):
            vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                'booking.order') or _('New')
        res = super(BookingOrder, self).create(vals)
        return res

    @api.model
    def create_book_order(self, partner_id, phone, pricelist, today, lines, note, pickup_date, deliver_date, delivery_address):
        print("lines", lines)
        values = []
        for l in lines:
            values.append((0, 0, {'product_id': l['product_id'],
                                  'qty': l['qty'],
                                  'discount': l['discount'],
                                  'tax_ids': l['taxes_id']
                                  }))

        order = self.create({
            'partner_id': partner_id,
            'phone': phone,
            'pricelist_id': pricelist,
            'date_quotation': today,
            'book_order': True,
            'lines': values,
            'note': note,
        })
        if pickup_date:
            order.write({'pickup_date': pickup_date})
        if deliver_date:
            order.write({'deliver_date': deliver_date,
                         'delivery_address': delivery_address,
                         })
        print('order----->', order)


class BookingOrderLine(models.Model):
    _name = 'book.order.line'

    order_id = fields.Many2one('booking.order', string='Order Ref', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)],
                                 required=True)
    price_unit = fields.Float(string='Unit Price', related='product_id.list_price')
    qty = fields.Float('Quantity', default=1)
    price_subtotal = fields.Float(string='Subtotal w/o Tax')
    price_subtotal_incl = fields.Float(compute='_compute_amount_line_all',
                                       string='Subtotal')
    discount = fields.Float(string='Discount', default=0.0)
    create_date = fields.Datetime(string='Creation Date', readonly=True)
    tax_ids = fields.Many2many('account.tax', string='Taxes')

    # @api.onchange('tax_ids')
    # def onchange_tax(self):
    #     print(self.tax_ids.amount,"tax")

    @api.depends('qty', 'price_unit', 'discount', 'tax_ids')
    def _compute_amount_line_all(self):
        for rec in self:
            rec.price_subtotal_incl = rec.price_unit * rec.qty
            if rec.tax_ids:
                print(rec.tax_ids.amount, "rec.tax_ids")
                print(rec.price_unit, "rec.price_unit")
                rec.price_subtotal_incl = rec.price_subtotal_incl + (
                        (rec.tax_ids.amount / rec.price_unit) * 100 * rec.qty)
            if rec.discount:
                rec.price_subtotal_incl = rec.price_subtotal_incl - rec.discount
