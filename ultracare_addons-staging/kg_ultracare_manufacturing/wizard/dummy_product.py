from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DummyProducts(models.TransientModel):
    _name = 'product.wise.dummy'
    _description = 'Dummy Products'

    user_id = fields.Many2one('res.users', string="Responsible", required=True,
                              default=lambda self: self.env.user and self.env.user.id or False)
    # dummy_product_id = fields.Many2one('product.product', string='Product', required=True)
    # actual_product_id = fields.Many2one('product.product', string='Product', required=True)
    production_plan_id = fields.Many2one('production.planning', string="Production Planning")
    shift_line_id = fields.Many2one('product.shift.line', string="Shift id")
    dummy_line_ids = fields.One2many('product.wise.dummy.line', 'dummy_id', string="Product Dummy Lines")

    def action_add_actual_products(self):
        vals = []
        for i in self.dummy_line_ids:
            # if i.actual_product_id.id in self.production_plan_id.kg_dummy_ids.mapped('kg_product_id').ids:
            #     raise UserError(
            #         _("This product is already selected in raw material.If you want to choose this product instead "
            #           "you can update it in dummy lines it self."))
            # else:
            if i.actual_product_id:
                i.dummy_line_id.update({'kg_product_id': i.actual_product_id.id,
                                        'product_uom_id': i.actual_product_id.uom_id.id })
                vals.append((0, 0, {'kg_product_id': i.dummy_product_id.id,
                                    'actual_product_id': i.actual_product_id.id,
                                    }))
        self.production_plan_id.write({'kg_dummy_product_ids': vals})
        return True


class DummyProductsLine(models.TransientModel):
    _name = 'product.wise.dummy.line'
    _description = 'Dummy Products Lines'

    dummy_product_id = fields.Many2one('product.product', string='Dummy Product', required=True)
    actual_product_id = fields.Many2one('product.product', string='Actual Product', required=True)
    production_plan_id = fields.Many2one('production.planning', string="Production Planning")
    shift_line_id = fields.Many2one('product.shift.line', string="Shift id")
    dummy_id = fields.Many2one('product.wise.dummy', 'Dummy ID')
    dummy_line_id = fields.Many2one('production.dummy.line', 'Dummy Line PP')
