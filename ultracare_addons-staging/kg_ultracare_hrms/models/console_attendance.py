from odoo import models, fields, tools


class ConsolAttend(models.Model):
    _name = "consol.attend"
    _description = "Consolidated Attendance"
    _auto = False

    name = fields.Char('Description', readonly=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', readonly=True)
    check_in = fields.Datetime('Check In', readonly=True)
    check_out = fields.Datetime('Check Out', readonly=True)
    attend_ids = fields.Char('Attend List', readonly=True)
    worked_hours = fields.Float(string='Worked Hours', readonly=True)
    attend_status = fields.Selection(
        [('leave', 'Leave'), ('halfday', 'Half Day'), ('present', 'Present'), ('present', 'Present'),
         ('punchmiss', 'Miss Punch')], readonly=True)

    _order = "check_in DESC"

    def init(self):
        a = tools.drop_view_if_exists(self._cr, 'consol_attend')
        self._cr.execute("""
            create or replace view consol_attend as (
            select
                        row_number() over(ORDER BY min(t.id)) as id,
                        min(t.id) as name,
                        t.employee_id as employee_id,
                        min(t.check_in) as check_in,
                        max(t.check_out) as check_out,
                        array_to_string(array_agg(t.id),',') as attend_ids
                   from hr_attendance t  group by check_in::date,t.employee_id
                   )""")
