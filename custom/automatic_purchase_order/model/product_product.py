from odoo import models

class AutomaticPO(models.Model):
    _inherit = 'product.product'

    def automatic_purchase_order(self):
        print("jjj")
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Automatic Purchase Order',
            'res_model': 'automaticpo.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_price': self.lst_price,
                        'default_product_id': self.id
                        }
        }
        return action
