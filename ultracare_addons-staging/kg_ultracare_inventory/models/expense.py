from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    user_rel_ids = fields.One2many('kg.users.line', 'kg_user_id', string="User Id")


class KgUserLine(models.Model):
    _name = 'kg.user.line'

    name = fields.Char()
    user_ids = fields.Many2one('res.users', string="Users")
    level = fields.Char(string="Level")
    kg_user_id = fields.Many2one('product.product', string="User")

    @api.onchange('user_ids')
    def onchange_users(self):
        length = 0
        for i in self:
            length += 1
            i.level = length + "Level"
