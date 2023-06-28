# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class kg_ultracare_sale(models.Model):
#     _name = 'kg_ultracare_sale.kg_ultracare_sale'
#     _description = 'kg_ultracare_sale.kg_ultracare_sale'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
