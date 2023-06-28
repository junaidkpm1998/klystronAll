from odoo import models, fields


class VehicleCharges(models.Model):
    _name = 'tm.estimation'

    estimation = fields.Many2one('tour.package')

    service = fields.Many2one('tm.service.types')
    quantity = fields.Integer()
    amount = fields.Integer()
    sub_total = fields.Integer(compute='sub_total_amount')
    # total_amount = fields.Integer(compute='total_amount_compute')

    def sub_total_amount(self):
        for rec in self:
            rec.sub_total = rec.amount * rec.quantity

    # def total_amount_compute(self):
    #     self.total_amount = sum(self.mapped('sub_total'))

