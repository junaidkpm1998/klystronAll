from odoo import models, fields, api, _


class ShiftMaster(models.Model):
    _name = 'shift.master'
    _description = 'Shift Master'

    name = fields.Char(string='Name')
    start_time = fields.Float(string="Start")
    end_time = fields.Float(string="End")
    end_am_pm = fields.Selection([('am', 'AM'),
                                  ('pm', 'PM')],
                                 required=True, default='pm')
    start_am_pm = fields.Selection([('am', 'AM'),
                                    ('pm', 'PM')],
                                   required=True, default='pm')
    percentage_threshold = fields.Float(string='Percent Threshold')
    kg_note = fields.Text(string="Note")
