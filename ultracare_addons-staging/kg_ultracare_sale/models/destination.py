from odoo import models, fields, api



class SubStageCRM(models.Model):
    _name = 'kg.destination'
    _description = 'Destination'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char('Destination')
    user_name = fields.Many2one('res.partner','Customer')
    company_name = fields.Many2one('res.company','Company')
