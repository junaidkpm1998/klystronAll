from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SpareType(models.Model):
    _name = 'kg.spare.type'
    _description = 'Spare Types'

    code = fields.Char("Code")
    name = fields.Char("Name")
    remarks = fields.Text("Remarks")
