from odoo import fields,models

class ProductTemplate(models.Model):
    _inherit = 'product.product'

    def automatic_sale_order(self):
        print("hhhh")
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Automatic Sale Order',
            'res_model': 'automaticso.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_price': self.lst_price,
                        'default_product_id': self.id

                        }
        }

        return action
