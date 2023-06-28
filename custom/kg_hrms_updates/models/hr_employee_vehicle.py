from datetime import date

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class EmployeeVehicle(models.Model):
    _name = 'employee.vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Vehicle Name', required=True, readonly=True, default=lambda self: _('New'))
    vehicle_model_id = fields.Many2one('hr.employee', required=True, string='Vehicle Model')
    owner_id = fields.Many2one('res.partner', required=True, string='Owner')
    insurance_number = fields.Text(required=True, string='Insurance Number')
    insurance_expiry = fields.Date(required=True, string='Insurance Expiry')
    fuel_card_number = fields.Text(required=True, string='Fuel Card Number')
    fuel_card_custodian_id = fields.Many2one('res.partner', required=True, string='Fuel Card Custodian')
    employee_id = fields.Many2one('hr.employee', required=True, string='Employee')
    start_date = fields.Date(required=True, string='Start Date')
    end_date = fields.Date(required=True, string='End Date')

    @api.model
    def create(self, vals):
        """autogenerating Vehicle name"""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'employee.vehicle') or _('New')
        res = super(EmployeeVehicle, self).create(vals)
        return res

    @api.onchange('insurance_expiry')
    def onchange_expiry_date(self):
        """validation error for expiry date which is less than current date"""
        today = date.today()
        insurance_expiry = self.insurance_expiry

        if insurance_expiry and insurance_expiry < today:
            raise ValidationError('The insurance expiry date should be choose greater than the current date')
