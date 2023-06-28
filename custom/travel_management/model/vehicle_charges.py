from odoo import models, fields


class VehicleCharges(models.Model):
    _name = 'vehicle.charges'

    charges = fields.Many2one('tm.vehicle')

    service = fields.Many2one('tm.service.types')
    quantity = fields.Integer()
    unit = fields.Integer()
    amount = fields.Integer()
