from odoo import models, fields


class TmServiceTypes(models.Model):
    _name = 'tm.service.types'

    name = fields.Text(string="Service types", required=True, options={'no_create': True})
    expiry_period = fields.Integer(string="expiration period")
    # jj = fields.Integer(string="jj")
