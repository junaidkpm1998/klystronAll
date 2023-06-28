from ast import literal_eval

from odoo import models, fields, api


class PurchaseOrderConfiguring(models.TransientModel):
    _inherit = 'res.config.settings'

    finance_ids = fields.Many2many('res.users', 'po_finance_rel', string='Finance')
    operations_ids = fields.Many2many('res.users', 'po_operations_rel', string='Operations')
    director_ids = fields.Many2many('res.users', 'po_manager_director_rel', string="Managing Director")
    kg_minimum_amount = fields.Monetary(related='po_double_validation_amount',string='Related Minimum Amount')

    def set_values(self):
        res = super(PurchaseOrderConfiguring, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('kg_ultracare_purchase.finance_ids', self.finance_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('kg_ultracare_purchase.operations_ids',
                                                         self.operations_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('kg_ultracare_purchase.director_ids', self.director_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('kg_ultracare_purchase.kg_minimum_amount', self.kg_minimum_amount)
        return res

    def get_values(self):
        sup = super(PurchaseOrderConfiguring, self).get_values()
        with_user = self.env['ir.config_parameter'].sudo()
        po_finance_partner = with_user.get_param('kg_ultracare_purchase.finance_ids')
        operation_partner = with_user.get_param('kg_ultracare_purchase.operations_ids')
        director_partner = with_user.get_param('kg_ultracare_purchase.director_ids')
        approve_amount = with_user.get_param('kg_ultracare_purchase.kg_minimum_amount')
        sup.update(finance_ids=[(6, 0, literal_eval(po_finance_partner))] if po_finance_partner else [],
                   operations_ids=[(6, 0, literal_eval(operation_partner))] if operation_partner else [],
                   director_ids=[(6, 0, literal_eval(director_partner))] if director_partner else [],
                   kg_minimum_amount = approve_amount)
        return sup

