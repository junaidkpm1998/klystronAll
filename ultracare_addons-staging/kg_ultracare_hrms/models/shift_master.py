from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class HrShift(models.Model):
    _name = 'hr.shift'
    _description = 'Labour Shift'

    name = fields.Char(
        string='Name',
        readonly=True, default='New', copy=False)
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee_id',
        required=True)
    start_date = fields.Date(
        string='Start Date',
        required=False)
    end_date = fields.Date(
        string='End Date',
        required=False)
    shift_type = fields.Selection(
        string='Shift Type',
        selection=[('day_shift', 'Day Shift'), ('night_shift', 'Night Shift') ],
        default = 'day_shift',
        required=True, )
    state = fields.Selection(
        string='Status',
        selection=[('draft', 'Draft'),
                   ('confirm', 'Confirmed'), ],
        default = 'draft',
        readonly=True, )


    @api.model
    def create(self, values):
        res = super(HrShift, self).create(values)
        res.name = res.employee_id.name + " : " + res.start_date.strftime('%d/%m/%Y') + '-' + res.end_date.strftime('%d/%m/%Y')
        return res

    def approve(self):
        for rec in self:
            rec.state = 'confirm'

    def reject(self):
        for rec in self:
            rec.state = 'draft'

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft'):
                raise UserError(_('You cannot delete a record which is not in draft state.'))
        return super(HrShift, self).unlink()

