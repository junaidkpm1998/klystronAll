from odoo import models, fields


class TravelManagementVehicle(models.Model):
    _name = 'tm.vehicle'
    _description = 'Travel Management Vehicle Model'
    _rec_name = 'reg_no'

    _sql_constraints = [('vehicle_reg_no_unique', 'unique(reg_no)', 'reg_no already exists')]

    reg_no = fields.Text(string="Registration NO", required=True)
    vehicle_types = fields.Selection([('bus', 'BUS'), ('traveller', 'TRAVELLER'), ('van', 'VAN'), ('other', 'OTHER')],
                                     required=True)
    name = fields.Text(compute='vehicle_name')
    no_seat = fields.Integer(default=1, string="Number of Seats")
    facilities = fields.Many2many('vehicle.facilities', string='Facilities')
    vehicle_charges = fields.One2many('vehicle.charges', 'charges', string='Vehicle Charges')

    def vehicle_name(self):
        self.name = self.reg_no + self.vehicle_types
        # return self.name
