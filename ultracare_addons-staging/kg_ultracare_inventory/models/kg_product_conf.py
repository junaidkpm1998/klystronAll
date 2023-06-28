from odoo import models, fields, api, _


class KgProductConf(models.Model):
    _name = 'kg.prod.conf'
    _description = 'Product Conf'

    name = fields.Char('Description')

    kg_shift_hours = fields.Float('Shift Hours')

    kg_no_of_shifts = fields.Float('No of Shifts')

    kg_month_days = fields.Integer('Month Days')

    kg_after_holidays = fields.Integer('After Holidays')

    kg_after_main = fields.Integer('After Maintenance')

    kg_global_eff = fields.Float('Global Efficency(%)')

    kg_quality_rate = fields.Float('Quality Rate(%)')

    active = fields.Boolean('Active', default=False)



    @api.onchange('kg_month_days')
    def onchange_month(self):
        self.kg_after_holidays = (self.kg_month_days) - 4

    @api.onchange('kg_after_holidays')
    def onchange_holidays(self):
        self.kg_after_main = (self.kg_after_holidays) - 4

    _sql_constraints = [
        ('active_uniq', 'unique (active)', "Only One Active Record Allowed!"),
    ]
