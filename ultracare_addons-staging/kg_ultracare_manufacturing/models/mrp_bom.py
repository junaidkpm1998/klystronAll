from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BillofMaterial(models.Model):
    _inherit = 'mrp.bom'
    _description = 'Bill of Material'

    name = fields.Char(string="Name")

    ## For Creating Bill of material name based on Type
    @api.onchange('product_tmpl_id', 'product_id', 'type')
    def onchange_material_tmpl_id(self):
        for i in self:
            if i.product_tmpl_id:
                type = i.type
                if i.type == 'normal':
                    i.name = "Normal" + ' : ' + i.product_tmpl_id.name
                else:
                    i.name = 'KIT' + ' : ' + i.product_tmpl_id.name

    # @api.constrains('bom_line_ids')
    # def _constrains_jumbo_roll(self):
    #     if not any(rec.product_id.jumbo_roll for rec in self.bom_line_ids):
    #         raise ValidationError(_('Please Select Jumbo Roll Enable Products Under Components'))


class BomLine(models.Model):
    _inherit = 'mrp.bom.line'
    _description = 'Bill of Material Lines'

    normal_wastage = fields.Float(string="Normal Wastage")
    jumbo_roll = fields.Boolean(string="Jumbo Roll", default=False)
