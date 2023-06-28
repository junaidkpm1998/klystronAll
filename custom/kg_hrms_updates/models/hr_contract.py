from datetime import timedelta, date
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrContract(models.Model):
    _inherit = 'hr.contract'

    probation = fields.Integer(string="Probation Period")
    basic = fields.Float(string='Basic')
    house_rent_allowance = fields.Float(string='House Rent Allowance')
    travel_allowance = fields.Float(string='Travel Allowance')
    bank_account_number = fields.Many2one('res.partner.bank', string='Bank Account Number')
    salary_compute_date = fields.Date(string='Date')

    @api.onchange('bank_account_number')
    def _onchange_bank_account_number(self):
        """Should not allow editing 7 days before salary computation"""
        today = date.today()
        if self.salary_compute_date:
            new_date = self.salary_compute_date + timedelta(days=-7)
            if (self.salary_compute_date >= today) and (today > new_date):
                raise ValidationError(_('Can not allow editing 7 days before salary computation'))
