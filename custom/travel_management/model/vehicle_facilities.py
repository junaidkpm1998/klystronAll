from odoo import models, fields


class TravelManagementVehicle(models.Model):
    _name = 'vehicle.facilities'
    _description = 'Travel Management Vehicle Facilities'

    name = fields.Char(string="Vehicle Facilities")
