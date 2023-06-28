from odoo import fields, models, api


class ProductReservation(models.Model):
    _name = 'product.reservation'

    name = fields.Char(string='Sequence Number', readonly=True, default=lambda self: "New")
    name_of_reservation = fields.Char()
    customer_id = fields.Many2one('res.partner')
    exp_date = fields.Date(string="Expiration Date")
    products_ids = fields.One2many('book.details', 'product_res')
    info = fields.Text()
    active = fields.Boolean(default=True)
    current_user_id = fields.Many2one('res.users', 'Current User', default=lambda self: self.env.user)


    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'product.reservation') or 'New'
        res = super(ProductReservation, self).create(vals)
        return res


