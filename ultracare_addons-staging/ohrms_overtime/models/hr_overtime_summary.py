from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class HrOverTimeSummary(models.Model):
    _name = 'hr.overtime.summary'
    _description = "HR Overtime Summary"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char('Name')
    date_from = fields.Datetime('Date From')
    date_to = fields.Datetime('Date To')
    overtime_id = fields.Many2one('hr.overtime')
    overtime_line_ids = fields.One2many('hr.overtime.summary.line', 'hr_ot_summary_id')
    overtime_ids = fields.One2many('hr.overtime', 'overtime_summary_id')
    is_fetch = fields.Boolean('Is Fetch', default=False)
    is_approve = fields.Boolean('Is Approve', default=False)

    def fetch_overtime_data(self):
        if self.date_from > self.date_to:
            raise ValidationError(_('Start Date must be less than End Date'))
        if self.date_from and self.date_to:
            overtime_id = self.env['hr.overtime'].search(
                [('state', '=', 'draft'), ('date_from', '>=', self.date_from),
                 ('date_to', '<=', self.date_to), ('overtime_summary_id', '=', False)])
            overtime_id.write({'overtime_summary_id': self.id})
            if overtime_id:
                self.is_fetch = True
                self.name = self.env['ir.sequence'].next_by_code('hr.overtime.summary.sequence')
            else:
                raise ValidationError(_("No overtime record in this date range"))

    def over_time_approve(self):
        for vals in self.overtime_ids:
            vals.approve()
            self.is_approve = True

    def over_time_reject(self):
        for vals in self.overtime_ids:
            vals.reject()
            self.is_approve = True


class HrOverTimeSummaryLine(models.Model):
    _name = 'hr.overtime.summary.line'
    _description = "HR Overtime Summary Line"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string='ID')
    over_time = fields.Many2one('hr.overtime')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    project_id = fields.Many2one('project.project', string="Project")
    date_from = fields.Datetime('Date From')
    date_to = fields.Datetime('Date to')
    days_no_tmp = fields.Float('Hours')
    state = fields.Selection([('draft', 'Draft'),
                              ('f_approve', 'Waiting'),
                              ('approved', 'Approved'),
                              ('refused', 'Refused')], string="state",
                             default="draft")
    type = fields.Selection([('cash', 'Cash'), ('leave', 'leave')], default="leave", required=True, string="Type",
                            readonly=True)
    payslip_paid = fields.Boolean('Paid in Payslip', readonly=True)
    hr_ot_summary_id = fields.Many2one('hr.overtime.summary', 'HR Overtime Summary')
