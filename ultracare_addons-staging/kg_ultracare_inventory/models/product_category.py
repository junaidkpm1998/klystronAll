from odoo import models, api, fields, tools, _

class Category(models.Model):
    _inherit = 'product.category'

    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id, string='Company')
