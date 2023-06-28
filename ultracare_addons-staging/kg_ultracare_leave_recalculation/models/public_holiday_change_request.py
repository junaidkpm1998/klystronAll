from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import datetime, date
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import timedelta, date

import pytz
from collections import namedtuple

Range = namedtuple('Range', ['start', 'end'])


class PublicHolidayChange(models.Model):
    _name = 'hr.public.holiday.change'
    _description = 'Change request for Public Holiday'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_user(self):
        return self.env.uid

    name = fields.Char(string='Reference No', required=True, copy=False,
                       readonly=True, index=True, default=lambda self: _('New'))
    user_id = fields.Many2one('res.users', string='User', readonly=True, default=_default_user)
    public_holiday_id = fields.Many2one('resource.calendar.leaves', 'Public Holiday', required=True, readonly=True,
                                        states={'draft': [('readonly', False)]}, domain="[('resource_id', '=', False)]")
    new_date_from = fields.Datetime(string='New From Date', readonly=True, required=True,
                                    states={'draft': [('readonly', False)]})
    new_date_to = fields.Datetime(string='New To Date', readonly=True, required=True,
                                  states={'draft': [('readonly', False)]})
    old_date_from = fields.Datetime(string='Current From Date', readonly=True)
    old_date_to = fields.Datetime(string='Current To Date', readonly=True)
    note = fields.Text(string='Notes')
    state = fields.Selection([('draft', 'Draft'), ('submit', 'Submit'), ('approve', 'Approved'), ('reject', 'Rejected'),
                              ('cancel', 'Cancel')],
                             string='State', default='draft', track_visibility='onchange', copy=False, )

    @api.onchange('public_holiday_id')
    def onchange_public_holiday_id(self):
        if self.public_holiday_id:
            self.old_date_from = self.public_holiday_id.date_from
            self.old_date_to = self.public_holiday_id.date_to

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.public.change') or _('New')
        request = super(PublicHolidayChange, self).create(vals)
        return request

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft'):
                raise UserError(_('You cannot delete a record which is not in draft state.'))
        return super(PublicHolidayChange, self).unlink()

    def action_confirm(self):
        for data in self:
            if data.old_date_from and data.old_date_to and data.new_date_from and data.new_date_to:
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                old_date_frm = datetime.strptime(
                    datetime.strftime(pytz.utc.localize(datetime.strptime(str(data.old_date_from),
                                                                          DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(
                        local), "%d/%m/%Y %H:%M%S"), "%d/%m/%Y %H:%M%S").date()
                old_date_to = datetime.strptime(
                    datetime.strftime(pytz.utc.localize(datetime.strptime(str(data.old_date_to),
                                                                          DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(
                        local), "%d/%m/%Y %H:%M%S"), "%d/%m/%Y %H:%M%S").date()
                new_date_frm = datetime.strptime(
                    datetime.strftime(pytz.utc.localize(datetime.strptime(str(data.new_date_from),
                                                                          DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(
                        local), "%d/%m/%Y %H:%M%S"), "%d/%m/%Y %H:%M%S").date()
                new_date_to = datetime.strptime(
                    datetime.strftime(pytz.utc.localize(datetime.strptime(str(data.new_date_to),
                                                                          DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(
                        local), "%d/%m/%Y %H:%M%S"), "%d/%m/%Y %H:%M%S").date()

                leaves = self.env['hr.leave'].search([])
                for i in leaves:
                    if i.request_date_to and i.request_date_from:
                        r1 = Range(start=old_date_frm, end=old_date_to)
                        r2 = Range(start=i.request_date_from, end=i.request_date_to)
                        old_latest_start = max(r1.start, r2.start)
                        old_earliest_end = min(r1.end, r2.end)
                        old_delta = (old_earliest_end - old_latest_start).days + 1
                        old_overlap = max(0, old_delta)

                        r3 = Range(start=new_date_frm, end=new_date_to)
                        new_latest_start = max(r3.start, r2.start)
                        new_earliest_end = min(r3.end, r2.end)
                        new_delta = (new_earliest_end - new_latest_start).days + 1
                        new_overlap = max(0, new_delta)

                        if old_overlap != new_overlap:
                            if old_overlap < new_overlap and i.employee_id:
                                check_alloc = self.env['hr.leave.allocation'].sudo().search(
                                    [('holiday_status_id', '=', i.holiday_status_id.id),
                                     ('public_holiday_id', '=', data.public_holiday_id.id),
                                     ('name','=','Public Holiday carry Forward')])
                                if not check_alloc:
                                    allocation = self.env['hr.leave.allocation'].create(
                                        {'name': 'Public Holiday carry Forward',
                                         'holiday_status_id': i.holiday_status_id.id,
                                         'holiday_type': 'employee',
                                         'allocation_type': 'regular',
                                         'date_from': date.today(),
                                         # 'date_end': date_end,
                                         'public_holiday_id': data.public_holiday_id.id,
                                         'number_of_days_display': new_overlap - old_overlap,
                                         'employee_id': i.employee_id.id,
                                         'notes': 'This leave created as compensatory for the public holiday ' + data.public_holiday_id.name,
                                         })
                                    allocation.action_confirm()
                                    allocation.action_validate()
                                i.write({'number_of_days': i.number_of_days + (new_overlap - old_overlap)})
                            else:
                                i.write({'number_of_days': i.number_of_days - (old_overlap - new_overlap)})

                data.public_holiday_id.write({'date_from': new_date_frm,
                                              'date_to': new_date_to})
                data.state = 'approve'

    def submit(self):
        for record in self:
            record.state = 'submit'

    def cancel(self):
        for record in self:
            record.state = 'cancel'

    def reset(self):
        for record in self:
            record.state = 'draft'

    def action_reject(self):
        for record in self:
            record.state = 'reject'
