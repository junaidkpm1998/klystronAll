from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RawMaterial(models.Model):
    _name = 'kg.raw.material'
    _description = 'Raw Material'

    product_id = fields.Many2one('product.product', string="Product")
    name = fields.Char("Name")
    material_tmpl_id = fields.Many2one('product.template')
    material_product_id = fields.Many2one('product.product')


class kg_spare_cat(models.Model):
    _name = 'kg.spare.cat'
    _description = 'Spare Category'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    remarks = fields.Text('Remarks')


class kg_machine(models.Model):
    _name = 'kg.machine'
    _description = 'Machine'

    name = fields.Char('Name', required=True)

    kg_speed_m_min = fields.Float('Speed m/min')

    remarks = fields.Text('Remarks')


class kg_mat_type(models.Model):
    _name = 'kg.mat.type'
    _description = 'Machine Type'

    name = fields.Char('Name', required=True)
    remarks = fields.Text('Remarks')


class kg_rm_type(models.Model):
    _name = 'kg.rm.type'
    _description = 'Raw Mateiral Type'

    name = fields.Char('Name', required=True)
    remarks = fields.Text('Remarks')
