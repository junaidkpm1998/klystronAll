# -*- coding: utf-8 -*-
import math

from dateutil import relativedelta
import pandas as pd

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.resource.models.resource import HOURS_PER_DAY

from odoo.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import pytz
from datetime import datetime


class HrOverTime(models.Model):
    _name = 'hr.overtime'
    _description = "HR Overtime"
    _inherit = ['mail.thread']

    def _get_employee_domain(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)], limit=1)
        domain = [('id', '=', employee.id)]
        if self.env.user.has_group('hr.group_hr_user'):
            domain = []
        return domain

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    @api.onchange('days_no_tmp')
    def _onchange_days_no_tmp(self):
        self.days_no = self.days_no_tmp

    name = fields.Char('Name', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  domain=_get_employee_domain, default=lambda self: self.env.user.employee_id.id,
                                  required=True)
    department_id = fields.Many2one('hr.department', string="Department",
                                    related="employee_id.department_id")
    job_id = fields.Many2one('hr.job', string="Job", related="employee_id.job_id")
    manager_id = fields.Many2one('res.users', string="Manager",
                                 related="employee_id.parent_id.user_id", store=True)
    current_user = fields.Many2one('res.users', string="Current User",
                                   related='employee_id.user_id',
                                   default=lambda self: self.env.uid,
                                   store=True)
    current_user_boolean = fields.Boolean()
    project_id = fields.Many2one('project.project', string="Project")
    project_manager_id = fields.Many2one('res.users', string="Project Manager")
    contract_id = fields.Many2one('hr.contract', string="Contract",
                                  related="employee_id.contract_id")
    date_from = fields.Datetime('Date From')
    date_to = fields.Datetime('Date to')
    days_no_tmp = fields.Float('Hours', compute="_get_days", store=True)
    days_no = fields.Float('No. of Days', store=True)
    desc = fields.Text('Description')
    state = fields.Selection([('draft', 'Draft'),
                              ('approved', 'Approved'),
                              ('refused', 'Refused')], string="state",
                             default="draft")
    cancel_reason = fields.Text('Refuse Reason')
    leave_id = fields.Many2one('hr.leave.allocation',
                               string="Leave ID")
    attchd_copy = fields.Binary('Attach A File')
    attchd_copy_name = fields.Char('File Name')
    type = fields.Selection([('cash', 'Cash'), ('leave', 'leave')], default="leave", required=True, string="Type",
                            readonly=True)
    overtime_type_id = fields.Many2one('overtime.type', domain="[('type','=',type),('duration_type','=', "
                                                               "duration_type)]")
    public_holiday = fields.Char(string='Public Holiday', readonly=True)
    attendance_ids = fields.Many2many('hr.attendance', string='Attendance')
    work_schedule = fields.One2many(
        related='employee_id.resource_calendar_id.attendance_ids')
    global_leaves = fields.One2many(
        related='employee_id.resource_calendar_id.global_leave_ids')
    duration_type = fields.Selection([('hours', 'Hour'), ('days', 'Days')], string="Duration Type", default="hours",
                                     required=True)
    cash_hrs_amount = fields.Float(string='Overtime Amount', readonly=True)
    cash_day_amount = fields.Float(string='Overtime Amount', readonly=True)
    payslip_paid = fields.Boolean('Paid in Payslip', readonly=True)

    over_time_day = fields.Selection(
        [('normal_days', 'Normal Days'), ('sunday', 'Sunday'), ('public_holidays', 'Public Holidays')],
        string="OverTime Days", store=True)
    ot_payment_new = fields.Float(string='OT Amount', readonly=True, compute="_compute_over_time_amount", store=True)
    ot_approve = fields.Boolean(string='Approve')
    overtime_summary_id = fields.Many2one('hr.overtime.summary', default=False)

    @api.depends('days_no_tmp', 'contract_id.basic_salary', 'over_time_day')
    def _compute_over_time_amount(self):
        """Compute Overtime Salary"""
        for rec in self:
            if rec.over_time_day == 'normal_days':
                rec.ot_payment_new = (
                        (((int(rec.contract_id.basic_salary) / 30) / 8) * 1.25) * math.ceil(rec.days_no_tmp))
            elif rec.over_time_day == 'sunday':
                rec.ot_payment_new = (((int(rec.contract_id.basic_salary) / 30) / 8) * 1.5) * math.ceil(rec.days_no_tmp)
            else:
                rec.ot_payment_new = (((int(rec.contract_id.basic_salary) / 30) / 8) * 1.5) * math.ceil(rec.days_no_tmp)

    @api.onchange('date_from', 'date_to', 'employee_id')
    def _onchange_date(self):
        holiday = False
        if self.contract_id and self.date_from and self.date_to:
            for leaves in self.contract_id.resource_calendar_id.global_leave_ids:
                leave_dates = pd.date_range(leaves.date_from, leaves.date_to).date
                overtime_dates = pd.date_range(self.date_from, self.date_to).date
                for over_time in overtime_dates:
                    for leave_date in leave_dates:
                        if leave_date == over_time:
                            holiday = True
            if holiday:
                self.write({
                    'public_holiday': 'You have Public Holidays in your Overtime request.',
                    'over_time_day': 'public_holidays'
                })
            else:
                if self.date_from:
                    date_from_day = self.date_from.strftime('%A')
                    holiday = ''
                    if date_from_day == 'Monday':
                        holiday = 'normal_days'
                    if date_from_day == 'Tuesday':
                        holiday = 'normal_days'
                    if date_from_day == 'Wednesday':
                        holiday = 'normal_days'
                    if date_from_day == 'Thursday':
                        holiday = 'normal_days'
                    if date_from_day == 'Friday':
                        holiday = 'normal_days'
                    if date_from_day == 'Saturday':
                        holiday = 'normal_days'
                    if date_from_day == 'Sunday':
                        holiday = 'sunday'

                self.write({'public_holiday': ' ', 'over_time_day': holiday})
            # hr_attendance = self.env['hr.attendance'].search(
            #     [('check_in', '>=', self.date_from),
            #      ('check_in', '<=', self.date_to),
            #      ('employee_id', '=', self.employee_id.id)])
            # self.update({
            #     'attendance_ids': [(6, 0, hr_attendance.ids)]
            # })

    @api.onchange('employee_id')
    def _get_defaults(self):
        for sheet in self:
            if sheet.employee_id:
                sheet.update({
                    'department_id': sheet.employee_id.department_id.id,
                    'job_id': sheet.employee_id.job_id.id,
                    'manager_id': sheet.sudo().employee_id.parent_id.user_id.id,
                })

    @api.depends('project_id')
    def _get_project_manager(self):
        for sheet in self:
            if sheet.project_id:
                sheet.update({
                    'project_manager_id': sheet.project_id.user_id.id,
                })

    @api.depends('date_from', 'date_to')
    def _get_days(self):
        for recd in self:
            if recd.date_from and recd.date_to:
                if recd.date_from > recd.date_to:
                    recd.update({
                        'days_no_tmp': 0.00,
                    })
                else:
                    for sheet in self:
                        if sheet.date_from and sheet.date_to:
                            start_dt = fields.Datetime.from_string(sheet.date_from)
                            finish_dt = fields.Datetime.from_string(sheet.date_to)
                            s = finish_dt - start_dt
                            difference = relativedelta.relativedelta(finish_dt, start_dt)
                            hours = difference.hours
                            minutes = difference.minutes
                            days_in_mins = s.days * 24 * 60
                            hours_in_mins = hours * 60
                            days_no = ((days_in_mins + hours_in_mins + minutes) / (24 * 60))

                            diff = sheet.date_to - sheet.date_from
                            days, seconds = diff.days, diff.seconds
                            print('days', days, 'seconds', seconds)
                            hours = round(days * 24 + seconds / 3600)
                            sheet.update({
                                'days_no_tmp': hours if sheet.duration_type == 'hours' else days_no,
                            })

    @api.onchange('overtime_type_id')
    def _get_hour_amount(self):
        if self.overtime_type_id.rule_line_ids and self.duration_type == 'hours':
            for recd in self.overtime_type_id.rule_line_ids:
                if recd.from_hrs < self.days_no_tmp <= recd.to_hrs and self.contract_id:
                    if self.contract_id.over_hour:
                        cash_amount = self.contract_id.over_hour * recd.hrs_amount
                        self.cash_hrs_amount = cash_amount
                    else:
                        raise UserError(_("Hour Overtime Needs Hour Wage in Employee Contract."))
        elif self.overtime_type_id.rule_line_ids and self.duration_type == 'days':
            for recd in self.overtime_type_id.rule_line_ids:
                if recd.from_hrs < self.days_no_tmp <= recd.to_hrs and self.contract_id:
                    if self.contract_id.over_day:
                        cash_amount = self.contract_id.over_day * recd.hrs_amount
                        self.cash_day_amount = cash_amount
                    else:
                        raise UserError(_("Day Overtime Needs Day Wage in Employee Contract."))

    def submit_to_f(self):
        # notification to employee
        recipient_partners = [(4, self.current_user.partner_id.id)]
        body = "Your OverTime Request Waiting Finance Approve .."
        msg = _(body)

        # notification to finance :
        group = self.env.ref('account.group_account_invoice', False)
        recipient_partners = []

        body = "You Get New Time in Lieu Request From Employee : " + str(
            self.employee_id.name)
        msg = _(body)
        return self.sudo().write({
            'state': 'f_approve'
        })

    def approve(self):
        self.ot_approve = True
        if self.overtime_type_id.type == 'leave':
            if self.duration_type == 'days':
                holiday_vals = {
                    'name': 'Overtime',
                    'holiday_status_id': self.overtime_type_id.leave_type.id,
                    'number_of_days': self.days_no_tmp,
                    'notes': self.desc,
                    'holiday_type': 'employee',
                    'employee_id': self.employee_id.id,
                    'state': 'validate',
                }
            else:
                day_hour = self.days_no_tmp / HOURS_PER_DAY
                holiday_vals = {
                    'name': 'Overtime',
                    'holiday_status_id': self.overtime_type_id.leave_type.id,
                    'number_of_days': day_hour,
                    'notes': self.desc,
                    'holiday_type': 'employee',
                    'employee_id': self.employee_id.id,
                    'state': 'validate',
                }
            holiday = self.env['hr.leave.allocation'].sudo().create(
                holiday_vals)
            self.leave_id = holiday.id

        work_entry_type = self.env['hr.work.entry.type'].search([('code', '=', 'OVERTIME001')])
        if work_entry_type and self.employee_id.name:
            name = work_entry_type.name + ": " + self.employee_id.name
        else:
            name = ''
        work_entry_data = {
            'name': name,
            'employee_id': self.employee_id.id,
            'work_entry_type_id': work_entry_type.id,
            'date_start': self.date_from,
            'date_stop': self.date_to,
            'duration': self.days_no_tmp
        }
        work_entry = self.env['hr.work.entry'].sudo().create(work_entry_data)

        # notification to employee :
        recipient_partners = [(4, self.current_user.partner_id.id)]
        body = "Your Time In Lieu Request Has been Approved ..."
        msg = _(body)
        return self.sudo().write({
            'state': 'approved',
        })

    def reject(self):
        self.state = 'refused'

    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for req in self:
            if req.days_no_tmp == 0.00:
                raise ValidationError('Start Datetime Must Be Less Than End Datetime')

            domain = [
                ('date_from', '<=', req.date_to),
                ('date_to', '>=', req.date_from),
                ('employee_id', '=', req.employee_id.id),
                ('id', '!=', req.id),
                ('state', 'not in', ['refused']),
            ]
            nholidays = self.search_count(domain)
            if nholidays:
                raise ValidationError(_(
                    'You can not have 2 Overtime requests that overlaps on same day!'))

    @api.model
    def create(self, values):
        seq = self.env['ir.sequence'].next_by_code('hr.overtime') or '/'
        values['name'] = seq
        return super(HrOverTime, self.sudo()).create(values)

    def unlink(self):
        for overtime in self.filtered(
                lambda overtime: overtime.state != 'draft'):
            raise UserError(
                _('You cannot delete TIL request which is not in draft state.'))
        return super(HrOverTime, self).unlink()


class HrOverTimeType(models.Model):
    _name = 'overtime.type'
    _description = "HR Overtime Type"

    name = fields.Char('Name')
    type = fields.Selection([('cash', 'Cash'),
                             ('leave', 'Leave ')])

    duration_type = fields.Selection([('hours', 'Hour'), ('days', 'Days')], string="Duration Type", default="hours",
                                     required=True)
    leave_type = fields.Many2one('hr.leave.type', string='Leave Type', domain="[('id', 'in', leave_compute)]")
    leave_compute = fields.Many2many('hr.leave.type', compute="_get_leave_type")
    rule_line_ids = fields.One2many('overtime.type.rule', 'type_line_id')

    @api.onchange('duration_type')
    def _get_leave_type(self):
        dur = ''
        ids = []
        if self.duration_type:
            if self.duration_type == 'days':
                dur = 'day'
            else:
                dur = 'hour'
            leave_type = self.env['hr.leave.type'].search([('request_unit', '=', dur)])
            for recd in leave_type:
                ids.append(recd.id)
            self.leave_compute = ids


class HrOverTimeTypeRule(models.Model):
    _name = 'overtime.type.rule'
    _description = "HR Overtime Type Rule"

    type_line_id = fields.Many2one('overtime.type', string='Over Time Type')
    name = fields.Char('Name', required=True)
    from_hrs = fields.Float('From', required=True)
    to_hrs = fields.Float('To', required=True)
    hrs_amount = fields.Float('Rate', required=True)
