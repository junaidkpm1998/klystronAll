from odoo import models, fields, api


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    ot_eligible = fields.Boolean('OT eligible', default=True)
    staff_type = fields.Selection([('office_staff', 'Office Staff'), ('labour', 'Labour')], default='labour',
                                  string='Staff Type')
    probation_completion_date = fields.Date('Probation Completion Date', required=True)
    shift_type = fields.Selection([('day_shift', 'Day Shift'), ('night_shift', 'Night Shift')], compute='_compute_shift',
                                  string='Shift Type')

    @api.onchange('staff_type')
    def _onchange_ot_eligible(self):
        for rec in self:
            if rec.staff_type == 'labour':
                rec.ot_eligible = True
            else:
                rec.ot_eligible = False

    def _compute_shift(self):
        for each in self:
            active_shift = self.env['hr.shift'].search([
                ('start_date', '<=', fields.Date.today()),
                ('end_date', '>=', fields.Date.today()),
                ('employee_id', '=', each.id)
            ], limit=1)
            if active_shift:
                each.shift_type = active_shift.shift_type
            else:
                each.shift_type = False

    def get_shift_in_period(self, date):
        for each in self:
            active_shift = self.env['hr.shift'].search([
                ('start_date', '<=', date),
                ('end_date', '>=', date),
                ('employee_id', '=', each.id)
            ], limit=1)
            if active_shift:
                return active_shift.shift_type
            else:
                return False
