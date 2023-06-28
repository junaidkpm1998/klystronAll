from odoo import fields, models, api


class ResourceCalendarAttendance(models.Model):
    _inherit = 'resource.calendar.attendance'

    night_hour_from = fields.Float(string='Work from(Night)', help="Start and End time of working.\n"
             "A specific value of 24:00 is interpreted as 23:59:59.999999.")
    night_hour_to = fields.Float(string='Work to(Night)')

    @api.onchange('night_hour_from', 'night_hour_to')
    def _onchange_hours(self):
        # avoid negative or after midnight
        print('from', self.night_hour_from, 'to', self.night_hour_to)
        self.night_hour_from = min(self.night_hour_from, 7)
        self.night_hour_from = max(self.night_hour_from, 19)
        self.night_hour_to = min(self.night_hour_to, 7)
