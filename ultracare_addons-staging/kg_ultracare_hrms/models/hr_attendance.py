from odoo import models, fields, api
from datetime import date, timedelta, time
import pandas as pd
from odoo.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import pytz
import logging
from pytz import timezone, utc
import datetime

_logger = logging.getLogger(__name__)


class HRAttendance(models.Model):
    _inherit = 'hr.attendance'

    normal_hours = fields.Float('Normal Hours', default=0.00)
    ot_hours = fields.Float('OT Hours', default=0.00, )
    is_approve = fields.Boolean(default=False)
    is_sec_approve = fields.Boolean(default=False)
    ot_time_from = fields.Datetime('OT From', default=False)
    overtime_id = fields.Many2one('hr.overtime', "Overtime")

    def tz_datetime(self, year, month, day, hour, minute):
        user_tz = self.env.user.tz or pytz.utc
        tz = pytz.timezone(user_tz)
        return tz.localize(datetime.datetime(year, month, day, hour, minute)).astimezone(pytz.utc).replace(tzinfo=None)

    def date_localize(self,dt):
        date3 = dt(pytz.timezone(self.env.user.tz or 'GMT')).strftime(
            "%d-%m-%Y %H:%M:%S:%z")
        return date3

    @api.model_create_multi
    def create(self, vals_list):
        res = super(HRAttendance, self).create(vals_list)
        res.compute_ot()
        return res

    @api.onchange('check_out', 'check_in', 'employee_id')
    @api.depends('check_out', 'check_in')
    def compute_ot(self):
        """Compute OT hours and Normal Hours"""
        for po in self:
            user_tz = self.env.user.tz or pytz.utc
            local = pytz.timezone(user_tz)
            if po.check_out:
                check_out_datetime = datetime.datetime.strftime(
                    pytz.utc.localize(datetime.datetime.strptime(str(po.check_out), DEFAULT_SERVER_DATETIME_FORMAT)).
                    astimezone(local), "%d/%m/%Y %H:%M:%S")
                check_out = datetime.datetime.strptime(check_out_datetime, '%d/%m/%Y %H:%M:%S')
                check_out_time = check_out.time()
                check_out_date = check_out.date()

                check_in_datetime = datetime.datetime.strftime(
                    pytz.utc.localize(datetime.datetime.strptime(str(po.check_in), DEFAULT_SERVER_DATETIME_FORMAT)).
                    astimezone(local), "%d/%m/%Y %H:%M:%S")
                check_in = datetime.datetime.strptime(check_in_datetime, '%d/%m/%Y %H:%M:%S')
                check_in_day_number = check_in.date().weekday()
                check_in_time = check_in.time()
                check_in_date = check_in.date()
                noon = datetime.datetime.strptime('01/01/2023 12:00:00', '%d/%m/%Y %H:%M:%S')
                noon_time = noon.time()
                if po.employee_id.staff_type == 'labour':
                    flag = False
                    public_holiday_count = self.env['resource.calendar.leaves'].search_count(
                        [('date_from', '>=', check_in_date), ('date_to', '<=', check_in_date)])
                    print('public_holiday_count', public_holiday_count)
                    if public_holiday_count > 0:
                        delta = po.check_out - po.check_in
                        ot_hours = delta.total_seconds() / 3600.0
                        po.write({
                            'ot_hours': ot_hours,
                            'normal_hours': 0.00,
                            'ot_time_from': po.check_in
                        })
                        return

                    resource_calendar = po.employee_id.resource_calendar_id.attendance_ids
                    for i in resource_calendar:
                        for j in i.dayofweek:
                            if int(j) == check_in_day_number:
                                print('j', j, 'check_in_day_number', check_in_day_number)
                                if i.day_period == 'afternoon':
                                    flag = True
                                    if po.employee_id.get_shift_in_period(check_in_date) == 'night_shift' and i.night_hour_to:
                                        hour_to_time_def = datetime.timedelta(hours=i.night_hour_to)
                                    else:
                                        hour_to_time_def = datetime.timedelta(hours=i.hour_to)
                                    hour_to_date_time = datetime.datetime.strptime(str(hour_to_time_def), '%H:%M:%S')
                                    hour_to_time = hour_to_date_time.time()
                                    hour_datetime = datetime.datetime.combine(check_out_date, hour_to_time)
                                    date_time = datetime.datetime.strptime(str(hour_datetime), "%Y-%m-%d %H:%M:%S")
                                    date_time_object = self.tz_datetime(date_time.year, date_time.month, date_time.day,
                                                                        date_time.hour, date_time.minute)

                                    # Day Shift
                                    if po.employee_id.get_shift_in_period(check_in_date) == 'day_shift':
                                        if check_in_time >= hour_to_time:
                                            OT_hours = datetime.datetime.combine(check_out_date, check_out_time) - datetime.datetime.combine(
                                                check_out_date, check_in_time)
                                            OT_hours_float_time = OT_hours.total_seconds() / 3600.0
                                        elif check_out_time > hour_to_time:
                                            OT_hours = datetime.datetime.combine(check_out_date, check_out_time) - datetime.datetime.combine(
                                                check_out_date, hour_to_time)
                                            OT_hours_float_time = OT_hours.total_seconds() / 3600.0
                                        else:
                                            OT_hours_float_time = 0
                                        normal_hours = po.worked_hours - OT_hours_float_time
                                        po.write({
                                            'ot_hours': OT_hours_float_time,
                                            'normal_hours': normal_hours,
                                            'ot_time_from': date_time_object,
                                        })

                                    #After normal Working hours
                                    elif check_in_time >= hour_to_time and check_in_time < noon_time and check_in_time <= check_out_time and po.employee_id.get_shift_in_period(check_in_date) == 'night_shift':
                                        if po.check_out and po.check_in:
                                            delta = po.check_out - po.check_in
                                            ot_hours = delta.total_seconds() / 3600.0
                                            self.write({
                                                'ot_hours': ot_hours,
                                                'normal_hours': 0.00,
                                                'ot_time_from': po.check_in
                                            })

                                    #Night Shift
                                    elif po.employee_id.get_shift_in_period(check_in_date) == 'night_shift':
                                        print('Night Shift')
                                        if check_in_time > noon_time and check_out_time > noon_time:
                                            OT_hours_float_time = 0
                                        elif check_in_time > noon_time and check_out_time < hour_to_time:
                                            OT_hours_float_time = 0
                                        elif check_out_time > hour_to_time:
                                            OT_hours = datetime.datetime.combine(check_out_date, check_out_time) - datetime.datetime.combine(
                                                check_out_date, hour_to_time)
                                            OT_hours_float_time = OT_hours.total_seconds() / 3600.0
                                        else:
                                            OT_hours_float_time = 0
                                        normal_hours = po.worked_hours - OT_hours_float_time
                                        po.write({
                                            'ot_hours': OT_hours_float_time,
                                            'normal_hours': normal_hours,
                                            'ot_time_from': date_time_object,
                                        })

                                    #Improper shift or wrong punch
                                    else:
                                        # print("Improper shift or wrong punch")
                                        if po.check_out and po.check_in:
                                            delta = po.check_out - po.check_in
                                            ot_hours = delta.total_seconds() / 3600.0
                                            self.write({
                                                'ot_hours': 0.00,
                                                'normal_hours': po.worked_hours,
                                                'ot_time_from': False
                                            })

                    #For Sunday or Weekend
                    if flag == False:
                        delta = po.check_out - po.check_in
                        ot_hours = delta.total_seconds() / 3600.0
                        po.write({
                            'ot_hours': ot_hours,
                            'normal_hours': 0.00,
                            'ot_time_from': po.check_in
                        })


    def action_approve(self):
        """PRODUCTION Approve Button action"""
        self.is_approve = True
        return True

    def second_action_approve(self):
        """HR Approve Button action"""

        for rec in self:
            rec.is_sec_approve = True
            if rec.ot_hours and rec.ot_time_from:
                overtime_request_data_1 = {
                    'employee_id': rec.employee_id.id,
                    'date_from': rec.ot_time_from,
                    'date_to': rec.check_out,
                }
                over_time_create_1 = self.env['hr.overtime'].sudo().create(overtime_request_data_1)
                self.overtime_id = over_time_create_1.id
                # over_time_create_1.attendance_ids.update({''})
                over_time_create_1._onchange_date()
                over_time_create_1._get_days()

            if rec.ot_hours and not rec.ot_time_from:
                overtime_request_data_2 = {
                    'employee_id': rec.employee_id.id,
                    'date_from': rec.check_in,
                    'date_to': rec.check_out,
                }
                over_time_create_2 = self.env['hr.overtime'].sudo().create(overtime_request_data_2)
                self.overtime_id = over_time_create_2.id
                over_time_create_2._onchange_date()
                over_time_create_2._get_days()


class HrOvertime(models.Model):
    _inherit = 'hr.overtime'

    att_ids = fields.One2many('hr.attendance', 'overtime_id', string="Attendances")
